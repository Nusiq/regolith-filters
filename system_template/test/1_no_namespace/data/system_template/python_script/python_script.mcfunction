output_lines: list[str] = []

for i in range(10):
    output_lines.append(f"say {i}")

output_lines.append(f"say variable_from_scope_direct = {variable_from_scope}")  # type: ignore
output_lines.append("say variable_from_scope_subfunctions = `eval:variable_from_scope`")

__output__ = "\n".join(output_lines)
