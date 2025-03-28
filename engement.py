import json
import re
import os

def load_usernames(file_path):
    """Load usernames from a text file, extracting '@username' from lines like '1:@username'."""
    usernames = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r"@\w+", line)
            if match:
                usernames.add(match.group())
    return usernames

def analyze_engagement(scraped_data, usernames):
    """Analyze engagement based on scraped post data. Ensure all users are included, even if engagement is 0%."""
    user_stats = {user: {"comments_made": 0, "missed": 0} for user in usernames}
    total_posts = len(scraped_data)  # Dynamic total posts

    for post in scraped_data:
        post_commenters = set(post["commenters"])  # Commenters in the current post
        for user in usernames:
            if user in post_commenters:
                user_stats[user]["comments_made"] += 1

    # Calculate missed comments and engagement percentage
    for user in usernames:
        user_stats[user]["missed"] = total_posts - user_stats[user]["comments_made"]
        user_stats[user]["percentage"] = round((user_stats[user]["comments_made"] / total_posts) * 100, 2) if total_posts > 0 else 0
        user_stats[user]["total_posts"] = total_posts  # Store total posts dynamically

    return user_stats

def save_results(user_stats):
    """Save engagement analysis to a separate folder."""
    output_folder = "engagement_results"
    os.makedirs(output_folder, exist_ok=True)
    
    # Save engagement percentage only with serial number
    report_path = os.path.join(output_folder, "engagement_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        for i, (user, stats) in enumerate(user_stats.items(), start=1):
            f.write(f"{i}. {user}: {stats['percentage']}%\n")  # No "Engagement" word

    # Save detailed engagement data (Same as before)
    details_path = os.path.join(output_folder, "engagement_details.txt")
    with open(details_path, "w", encoding="utf-8") as f:
        for user, stats in user_stats.items():
            f.write(f"{user} - Comments: {stats['comments_made']}, Missed: {stats['missed']}, Percentage: {stats['percentage']}%\n")

    # Generate report.txt (NEW File as per request)
    report_file = os.path.join(output_folder, "report.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        for i, (user, stats) in enumerate(user_stats.items(), start=1):
            f.write(f"{i}: {user}: {stats['comments_made']} out of {stats['total_posts']} - {stats['percentage']}%\n")

def main():
    usernames = load_usernames("usernames.txt")
    with open("collected_posts.json", "r", encoding="utf-8") as f:
        scraped_data = json.load(f)
    
    user_stats = analyze_engagement(scraped_data, usernames)
    save_results(user_stats)
    print("✅ Engagement analysis completed. Results saved in 'engagement_results' folder.")

if __name__ == "__main__":
    main()
