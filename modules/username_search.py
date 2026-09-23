"""
ReconX – Username Intelligence Module
Searches a username across 30+ platforms concurrently.
"""

import concurrent.futures
from utils.api_clients import check_username_on_platform
from utils.logger import get_logger

logger = get_logger("username_search")

# Platform definitions: name -> URL template with {username} placeholder
PLATFORMS = {
    "GitHub":         "https://github.com/{username}",
    "GitLab":         "https://gitlab.com/{username}",
    "Reddit":         "https://www.reddit.com/user/{username}",
    "Twitter/X":      "https://twitter.com/{username}",
    "Instagram":      "https://www.instagram.com/{username}",
    "TikTok":         "https://www.tiktok.com/@{username}",
    "Pinterest":      "https://www.pinterest.com/{username}",
    "YouTube":        "https://www.youtube.com/@{username}",
    "Twitch":         "https://www.twitch.tv/{username}",
    "Tumblr":         "https://www.tumblr.com/{username}",
    "Medium":         "https://medium.com/@{username}",
    "Dev.to":         "https://dev.to/{username}",
    "Hashnode":       "https://hashnode.com/@{username}",
    "Patreon":        "https://www.patreon.com/{username}",
    "Keybase":        "https://keybase.io/{username}",
    "HackerNews":     "https://news.ycombinator.com/user?id={username}",
    "ProductHunt":    "https://www.producthunt.com/@{username}",
    "Steam":          "https://steamcommunity.com/id/{username}",
    "Fiverr":         "https://www.fiverr.com/{username}",
    "Behance":        "https://www.behance.net/{username}",
    "Dribbble":       "https://dribbble.com/{username}",
    "SoundCloud":     "https://soundcloud.com/{username}",
    "Spotify":        "https://open.spotify.com/user/{username}",
    "Flickr":         "https://www.flickr.com/people/{username}",
    "Vimeo":          "https://vimeo.com/{username}",
    "Codepen":        "https://codepen.io/{username}",
    "Replit":         "https://replit.com/@{username}",
    "HuggingFace":    "https://huggingface.co/{username}",
    "Kaggle":         "https://www.kaggle.com/{username}",
    "DockerHub":      "https://hub.docker.com/u/{username}",
    "NPMjs":          "https://www.npmjs.com/~{username}",
    "PyPI":           "https://pypi.org/user/{username}",
    "StackOverflow":  "https://stackoverflow.com/users/{username}",
    "Linktree":       "https://linktr.ee/{username}",
    "Gravatar":       "https://en.gravatar.com/{username}",
}


def search_username(username: str, progress_callback=None) -> dict:
    """
    Search for a username across all configured platforms.

    Args:
        username: The username to search.
        progress_callback: Optional callable(platform, result) called after each check.

    Returns:
        dict with keys 'username', 'found', 'not_found', 'errors', 'total'
    """
    username = username.strip()
    logger.info(f"Starting username search for: {username}")

    results = {
        "username": username,
        "found": {},
        "not_found": [],
        "errors": {},
        "total": len(PLATFORMS),
    }

    def check(platform_name):
        url_template = PLATFORMS[platform_name]
        result = check_username_on_platform(url_template, username)
        if progress_callback:
            progress_callback(platform_name, result)
        return platform_name, result

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check, name): name for name in PLATFORMS}
        for future in concurrent.futures.as_completed(futures):
            try:
                name, res = future.result()
                if res.get("error"):
                    results["errors"][name] = res["error"]
                elif res["found"]:
                    results["found"][name] = res["url"]
                else:
                    results["not_found"].append(name)
            except Exception as e:
                pname = futures[future]
                logger.error(f"Unexpected error for {pname}: {e}")
                results["errors"][pname] = str(e)

    logger.info(
        f"Username '{username}': found on {len(results['found'])}/{results['total']} platforms."
    )
    return results
