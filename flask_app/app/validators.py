from dataclasses import dataclass


@dataclass
class ValidationResult:
    first_name: str
    last_name: str


class ValidationError(Exception):
    def __init__(self, messages: list[str]):
        super().__init__("; ".join(messages))
        self.messages = messages


def validate_names(first_name: str, last_name: str, max_length: int) -> ValidationResult:
    errors: list[str] = []
    clean_first = (first_name or "").strip()
    clean_last = (last_name or "").strip()

    if not clean_first:
        errors.append("First name is required.")
    if not clean_last:
        errors.append("Last name is required.")
    if len(clean_first) > max_length:
        errors.append(f"First name must be at most {max_length} characters.")
    if len(clean_last) > max_length:
        errors.append(f"Last name must be at most {max_length} characters.")

    if errors:
        raise ValidationError(errors)

    return ValidationResult(first_name=clean_first, last_name=clean_last)
