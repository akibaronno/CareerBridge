

from app.helpers import open_jobs_query


def calculate_match(job, seeker):
    """
    score = (required skills the candidate has / required skills) * 100
    Returns a dict with the score and the matched / missing skill names.
    """
    required = list(job.skills)
    have_ids = {s.id for s in seeker.skills} if seeker else set()
    matched = [s.name for s in required if s.id in have_ids]
    missing = [s.name for s in required if s.id not in have_ids]
    score = round(len(matched) / len(required) * 100) if required else 0
    return {"score": score, "matched": matched, "missing": missing}


def recommended_jobs(seeker, limit=6):
    """Open jobs (not applied yet) ranked by match score, best first."""
    if not seeker:
        return []
    applied = {a.job_id for a in seeker.applications}
    results = []
    for job in open_jobs_query().all():
        if job.id in applied:
            continue
        m = calculate_match(job, seeker)
        if m["score"] > 0:
            results.append((job, m))
    results.sort(key=lambda r: r[1]["score"], reverse=True)
    return results[:limit]
