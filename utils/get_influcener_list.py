def get_unique_influencers(weekly_data) -> list:
    """
    Given the weekly_data dict (from build_report_category_summary_dict),
    returns a sorted list of unique influencer names/handles.
    """
    unique_influencers = set()
    for report in weekly_data.values():
        for summary, influencers in report["categories"].values():
            unique_influencers.update(influencers)
    return sorted(unique_influencers)