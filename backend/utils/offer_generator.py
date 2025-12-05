from datetime import date


def generate_offer(title: str = "Offer", candidate_name: str | None = None) -> str:
    name = candidate_name or "Candidate"
    today = date.today().isoformat()
    body = (
        f"{title}\n\n"
        f"Dear {name},\n\n"
        f"We are pleased to extend to you an offer of employment at Our Company as a Software Engineer.\n"
        f"Start Date: TBD\n"
        f"Compensation: Competitive package including base, bonus, and benefits.\n\n"
        f"This offer is contingent upon successful completion of the interview process and onboarding steps,\n"
        f"including scheduling, background checks (if applicable), and enrollment in our training LMS.\n\n"
        f"Next Steps:\n"
        f"1) Confirm your availability via the scheduling portal.\n"
        f"2) Review and accept the attached offer terms.\n"
        f"3) Enroll in the onboarding course to begin your training modules and labs.\n\n"
        f"We look forward to working with you.\n\n"
        f"Sincerely,\n"
        f"Talent Team\n"
        f"Date: {today}\n"
    )
    return body