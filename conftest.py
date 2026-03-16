import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--k8s",
        action="store_true",
        default=False,
        help="Run Kubernetes integration tests against the current kubeconfig context",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "k8s: mark test as a Kubernetes integration test (requires --k8s flag)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--k8s"):
        # Only run k8s-marked tests
        selected = [item for item in items if "k8s" in item.keywords]
        deselected = [item for item in items if "k8s" not in item.keywords]
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected
        return
    skip_k8s = pytest.mark.skip(
        reason="Need --k8s flag to run Kubernetes integration tests"
    )
    for item in items:
        if "k8s" in item.keywords:
            item.add_marker(skip_k8s)
