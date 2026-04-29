from services import stats

def enrich_posts_with_likes_and_ratings(posts, uid):
    if not posts:
        return posts

    ids = [p["id"] for p in posts]

    like_counts = stats.get_like_counts_for_posts(ids)
    liked_set = stats.get_liked_set_for_user(uid, ids) if uid else set()
    rating_stats = stats.get_rating_stats_for_posts(ids)
    my_ratings = stats.get_my_ratings_for_user(uid, ids) if uid else {}

    for p in posts:
        pid = p["id"]
        p["like_count"] = like_counts.get(pid, 0) if "like_count" not in p else p["like_count"]
        p["liked_by_me"] = pid in liked_set
        avg, cnt = rating_stats.get(pid, (None, 0))
        p["avg_rating"] = avg
        p["rating_count"] = cnt
        p["my_rating"] = my_ratings.get(pid)

    return posts
