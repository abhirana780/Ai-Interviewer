def enroll_message(course_name: str) -> str:
    name = course_name or "Onboarding"
    return (
        f"Enrollment confirmed for course: {name}.\n"
        f"You will have access to AI tutors, autograded labs, and project assignments.\n"
        f"Please check your dashboard for modules and due dates."
    )