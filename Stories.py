import streamlit as st
import requests
from datetime import datetime, timedelta

# YouTube API Key (Store securely in Streamlit secrets)
API_KEY = st.secrets["youtube_api_key"]
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
min_views = st.number_input("Minimum Views Threshold:", min_value=1000, value=5000)
max_results = st.slider("Results per Keyword:", min_value=5, max_value=50, value=10)

# List of broader keywords
keywords = [
    "Stories"
]

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        # Iterate over the list of keywords
        for keyword in keywords:
            with st.spinner(f"Searching for keyword: {keyword}..."):
                # Define search parameters
                search_params = {
                    "part": "snippet",
                    "q": keyword,
                    "type": "video",
                    "order": "viewCount",
                    "publishedAfter": start_date,
                    "maxResults": max_results,
                    "relevanceLanguage": "en",
                    "regionCode": "US",  # Target specific regions
                    "videoDuration": "medium",  # Focus on 4-20min videos
                    "key": API_KEY,
                }

                # Fetch video data
                response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
                data = response.json()

                # Check if "items" key exists
                if "items" not in data or not data["items"]:
                    st.warning(f"No videos found for keyword: {keyword}")
                    continue

                videos = data["items"]
                video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
                channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

                if not video_ids or not channel_ids:
                    st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.")
                    continue

                # Fetch video statistics
                stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
                stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
                stats_data = stats_response.json()

                if "items" not in stats_data or not stats_data["items"]:
                    st.warning(f"Failed to fetch video statistics for keyword: {keyword}")
                    continue

                # Fetch channel statistics
                channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
                channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
                channel_data = channel_response.json()

                if "items" not in channel_data or not channel_data["items"]:
                    st.warning(f"Failed to fetch channel statistics for keyword: {keyword}")
                    continue

                stats = stats_data["items"]
                channels = channel_data["items"]

                # Collect results
                for i in range(len(videos)):
                    video = videos[i]
                    stat = stats[i] if i < len(stats) else {}
                    channel = channels[i] if i < len(channels) else {}

                    title = video["snippet"].get("title", "N/A")
                    description = video["snippet"].get("description", "")[:200]
                    video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                    views = int(stat["statistics"].get("viewCount", 0))
                    subs = int(channel["statistics"].get("subscriberCount", 0))
                    likes = int(stat["statistics"].get("likeCount", 0))
                    engagement_ratio = (likes / views) if views > 0 else 0
                    view_subs_ratio = (views / subs) if subs > 0 else 0

                    # Filter for viral potential
                    if (subs < 5000 and views >= min_views and engagement_ratio > 0.05 and view_subs_ratio > 100):
                        all_results.append({
                            "Title": title,
                            "Description": description,
                            "URL": video_url,
                            "Views": views,
                            "Subscribers": subs,
                            "Engagement Ratio": f"{engagement_ratio:.2%}",
                            "View/Sub Ratio": f"{view_subs_ratio:.1f}"
                        })

        # Display results
        if all_results:
            st.success(f"Found {len(all_results)} results across all keywords!")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}  \n"
                    f"**Engagement Ratio:** {result['Engagement Ratio']}  \n"
                    f"**View/Sub Ratio:** {result['View/Sub Ratio']}"
                )
                st.write("---")
        else:
            st.warning("No results found for channels with fewer than 5,000 subscribers.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
