from agents import JobAgent, MatchingAgent, RecommendationAgent, ResumeAgent, ReviewAgent


def run_pipeline(resume_text: str, job_text: str):
    """Run all agents sequentially and return their individual results."""
    resume_agent = ResumeAgent()
    job_agent = JobAgent()
    matching_agent = MatchingAgent()
    recommendation_agent = RecommendationAgent()
    review_agent = ReviewAgent()

    resume_result = resume_agent.run(resume_text)
    job_result = job_agent.run(job_text)
    matching_result = matching_agent.run(resume_result, job_result)
    recommendation_result = recommendation_agent.run(
        resume_result,
        job_result,
        matching_result,
    )
    review_result = review_agent.run(
        resume_result,
        job_result,
        matching_result,
        recommendation_result,
    )

    return {
        "resume": resume_result,
        "job": job_result,
        "matching": matching_result,
        "recommendation": recommendation_result,
        "review": review_result,
    }
