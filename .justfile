api:
    rye run python main.py --transport streamable-http --port 8321


dev:
    #!/usr/bin/env bash

    if command -v watchexec >/dev/null 2>&1; then
        watchexec \
            --watch src \
            --ignore tests \
            --ignore benches \
            --exts py \
            --on-busy-update=restart \
            --stop-signal SIGKILL \
            -- rye run python main.py --transport streamable-http --port 8321 --app-dir datatable_tools/
    else
        rye run python main.py --transport streamable-http --port 8321 --reload --reload-dir datatable_tools/ 
    fi

format:
    rye run isort --profile=black --skip-gitignore .
    rye run ruff check --fix --exit-zero .
    rye run ruff format .

format-file PATH:
    rye run isort --profile=black --skip-gitignore {{PATH}}
    rye run ruff check --fix --exit-zero {{PATH}}
    rye run ruff format {{PATH}}
