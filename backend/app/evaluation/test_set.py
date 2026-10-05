# Each entry: a realistic question, plus the symbol name(s) that count as
# a correct answer. We already confirmed these by hand across Days 12-21.
TEST_QUESTIONS = [
    {
        "question": "how does Flask register a URL route?",
        "repo": "pallets/flask",
        "correct_symbols": ["add_url_rule", "route"],
    },
    {
        "question": "how does Flask handle errors raised during a request?",
        "repo": "pallets/flask",
        "correct_symbols": ["_find_error_handler", "register_error_handler", "handle_user_exception"],
    },
    {
        "question": "how are blueprints registered on an app?",
        "repo": "pallets/flask",
        "correct_symbols": ["register_blueprint", "BlueprintSetupState"],
    },
    {
        "question": "_get_exc_class_and_code",
        "repo": "pallets/flask",
        "correct_symbols": ["_get_exc_class_and_code"],
    },
    {
        "question": "how does Flask manage application context?",
        "repo": "pallets/flask",
        "correct_symbols": ["AppContext", "push", "pop"],
    },
    # Harder / less rehearsed cases below
    {
        "question": "how does Flask decide which config values to load from a file?",
        "repo": "pallets/flask",
        "correct_symbols": ["from_pyfile", "from_object", "from_mapping", "from_envvar"],
    },
    {
        "question": "how does Flask serialize JSON responses?",
        "repo": "pallets/flask",
        "correct_symbols": ["jsonify", "dumps", "JSONProvider"],
    },
    {
        "question": "what happens when a session cookie is tampered with?",
        "repo": "pallets/flask",
        "correct_symbols": ["open_session", "SecureCookieSessionInterface"],
    },
    {
        "question": "how does Flask's CLI discover the app to run?",
        "repo": "pallets/flask",
        "correct_symbols": ["locate_app", "find_best_app", "NoAppException"],
    },
]