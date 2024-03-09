import requests


def get_bilibili_sub(bid, lang):

    #bid = "BV1jx421y7TP"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
            }
    
    api_link = f"https://api.bilibili.com/x/player/pagelist?bvid={bid}&jsonp=jsonp"
    
    response = requests.get(api_link, headers=header).json()
    
    cid = response["data"][0]["cid"]
    
    video_link = f"https://api.bilibili.com/x/web-interface/view?bvid={bid}&cid={cid}"
    
    response = requests.get(video_link, headers=header).json()
    
    title = response["data"]["title"]
    desc = response["data"]["desc"]
    subtitle = response["data"]["subtitle"]["allow_submit"]
    
    aid = response["data"]["aid"]
    
    #print(f"Title: {title}\nDescription: {desc}\nSubtitle: {subtitle}")
    
    #new_link = f"https://api.bilibili.com/x/player/v2?cid={cid}&aid={aid}:&bvid={bid}"
    new_link = f"https://api.bilibili.com/x/v2/dm/view?aid={aid}&bvid={bid}&oid={cid}&type=1"
    
    response = requests.get(new_link, headers=header).json()
    
    subtitle_url = [s for s in response["data"]["subtitle"]["subtitles"] if lang in s["lan"]][0]["subtitle_url"]
    
    subtitle = requests.get(subtitle_url, headers=header).json()
    subtitle_list = subtitle["body"]
    
    """
    {'from': 5.16, 'to': 8.8, 'sid': 1, 'location': 2, 'content': '哎呀开局就做人了', 'music': 0.0}
    """
    
    return subtitle_list
