ARC3_SERVING_PATCHES = [
    [
        "VLLM_MAX_MODEL_LEN = 65536",
        "VLLM_MAX_MODEL_LEN = 32768"
    ],
    [
        "ANALYZER_CONTEXT_WINDOW = 32768",
        "ANALYZER_CONTEXT_WINDOW = 24576"
    ],
    [
        "'LOCAL_ANALYZER_MAX_OUTPUT': '0'",
        "'LOCAL_ANALYZER_MAX_OUTPUT': '3072'"
    ],
    [
        "'LOCAL_ANALYZER_TOOL_STEPS': '0'",
        "'LOCAL_ANALYZER_TOOL_STEPS': '12'"
    ]
]

import re


def _source_path_entries(bundle_dir: Path) -> list[Path]:
    src_root = bundle_dir / "src"
    if not src_root.is_dir():
        return []

    entries: list[Path] = []
    for repo in sorted(src_root.iterdir(), reverse=True):
        if not repo.is_dir():
            continue
        for candidate in (repo / "src", repo):
            if candidate.is_dir():
                entries.append(candidate)
    return entries


def _command_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHON"] = sys.executable
    env["TAAF_KAGGLE_BUNDLE_DIR"] = str(BUNDLE_DIR)
    env["TAAF_KAGGLE_WORKING_DIR"] = str(WORKING_DIR)
    env["TAAF_KAGGLE_SETUP_ENV"] = str(SETUP_ENV_PATH)
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"
    env.update(_load_setup_env())
    return env


def _replace_python_assignment(
    command: str,
    variable_name: str,
    value: str,
) -> tuple[str, int]:
    """Replace a top-level Python string assignment inside the setup here-doc."""
    pattern = rf"(?m)^{re.escape(variable_name)}\s*=\s*(['\"])[^\r\n]*?\1\s*$"
    replacement = f"{variable_name} = {value!r}"
    return re.subn(pattern, replacement, command, count=1)


def _patch_qwen38_setup_commands(commands: list[str]) -> list[str]:
    """
    Preserve the TAAF deployment setup but replace its model identity with the
    Qwen3.8 Kaggle Model. This avoids copying/forking the large bundled setup
    script and keeps the wheelhouse/GPU/vLLM behavior from the source bundle.
    """
    patched: list[str] = []
    replacement_counts = {
        "MODEL_OWNER": 0,
        "MODEL_SLUG": 0,
        "SERVED_MODEL_NAME": 0,
    }

    replacements = {
        "MODEL_OWNER": QWEN_MODEL_OWNER,
        "MODEL_SLUG": QWEN_MODEL_SLUG,
        "SERVED_MODEL_NAME": QWEN_SERVED_MODEL_NAME,
    }

    for raw_command in commands:
        command = str(raw_command)

        for variable_name, value in replacements.items():
            command, count = _replace_python_assignment(
                command,
                variable_name,
                value,
            )
            replacement_counts[variable_name] += count

        # Make offline behavior explicit in the child process as well.
        if "def vllm_env()" in command:
            command = command.replace(
                "'VLLM_NO_USAGE_STATS': '1',",
                "'VLLM_NO_USAGE_STATS': '1',\n"
                "            'HF_HUB_OFFLINE': '1',\n"
                "            'TRANSFORMERS_OFFLINE': '1',",
                1,
            )

        # arc3 item 2: bound the runaway turn and stop paying for a served context
        # window the agent never asks for (both shipped as unlimited / 2x oversized).
        for _old, _new in ARC3_SERVING_PATCHES:
            if _old in command:
                command = command.replace(_old, _new)
                print('arc3 serving patch:', _old, '->', _new, flush=True)
        patched.append(command)

    missing = [
        name for name, count in replacement_counts.items() if count == 0
    ]
    if missing:
        raise RuntimeError(
            "Could not update the bundled TAAF setup for Qwen3.8. "
            "Missing assignment(s): "
            + ", ".join(missing)
            + ". The attached TAAF bundle's setup_commands.json has changed."
        )

    print("taaf.kaggle: Qwen3.8 setup patch =", replacement_counts, flush=True)
    return patched


def _run_shell_commands(filename: str, *, label: str, check: bool) -> None:
    path = BUNDLE_DIR / filename
    if not path.is_file():
        return

    commands = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(commands, list):
        raise RuntimeError(f"{path} must contain a JSON list of shell commands.")

    if filename == "setup_commands.json":
        commands = _patch_qwen38_setup_commands(commands)

    env = _command_env()
    for command in commands:
        print(f"taaf.kaggle: {label} command: {command}", flush=True)
        result = subprocess.run(
            str(command),
            shell=True,
            check=check,
            cwd=WORKING_DIR,
            env=env,
        )
        if not check and result.returncode != 0:
            print(
                f"taaf.kaggle: {label} command exited with {result.returncode}",
                flush=True,
            )

        # Setup commands may export additional runtime settings.
        env.update(_load_setup_env())
        os.environ.update(env)


# Make bundled TAAF repos importable for this notebook and child Python processes.
source_entries = _source_path_entries(BUNDLE_DIR)
for entry in source_entries:
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

if source_entries:
    import sysconfig

    pth_path = Path(sysconfig.get_paths()["purelib"]) / "taaf_kaggle_sources.pth"
    pth_path.write_text(
        "".join(f"{entry}\n" for entry in source_entries),
        encoding="utf-8",
    )
    print(
        f"taaf.kaggle: wrote {pth_path} ({len(source_entries)} source roots)",
        flush=True,
    )

# Run the TAAF deployment setup, patched to use Qwen3.8.
_run_shell_commands("setup_commands.json", label="setup", check=True)

# Setup commands may export PYTHONPATH through TAAF_KAGGLE_SETUP_ENV.
pythonpath_entries = [
    entry for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep) if entry
]
for entry in reversed(pythonpath_entries):
    if entry not in sys.path:
        sys.path.insert(0, entry)

# Fail early if the analyzer is still exposing an old model identity.
_actual_model_id = os.environ.get("INFERENCE_ANALYZER_MODEL", "")
if _actual_model_id != QWEN_SERVED_MODEL_NAME:
    raise RuntimeError(
        "TAAF setup completed, but the analyzer model ID is wrong: "
        f"{_actual_model_id!r}; expected {QWEN_SERVED_MODEL_NAME!r}"
    )

print("\n✅ TAAF/vLLM setup completed for Qwen3.8")
print("Model path:", QWEN_MODEL_PATH)
print("Analyzer model:", _actual_model_id)
print("Analyzer endpoint:", os.environ.get("LOCAL_ANALYZER_BASE_URL"))
