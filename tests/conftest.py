import pytest

def pytest_configure(config):
    # Define a default base-url if none is specified by the user
    if not config.getoption("--base-url"):
        config.option.base_url = "http://localhost:5173"

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {
            "width": 1280,
            "height": 800,
        },
        "ignore_https_errors": True,
    }
