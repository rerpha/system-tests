from datetime import datetime
import os.path
import pytest
from compose.cli.main import TopLevelCommand, project_from_options
from confluent_kafka.admin import AdminClient
from confluent_kafka import Producer
from time import sleep

from helpers.timehelpers import unix_time_milliseconds


def wait_until_kafka_ready(docker_cmd, docker_options):
    print("Waiting for Kafka broker to be ready for system tests...", flush=True)
    conf = {
        "bootstrap.servers": "localhost:9092",
        "metadata.request.timeout.ms": "10000",
    }
    producer = Producer(**conf)

    kafka_ready = False

    def delivery_callback(err, msg):
        nonlocal n_polls
        nonlocal kafka_ready
        if not err:
            print("Kafka is ready!")
            kafka_ready = True

    n_polls = 0
    while n_polls < 10 and not kafka_ready:
        producer.produce(
            "waitUntilUp", value="Test message", on_delivery=delivery_callback
        )
        producer.poll(10)
        n_polls += 1

    if not kafka_ready:
        docker_cmd.down(docker_options)  # Bring down containers cleanly
        raise Exception("Kafka broker was not ready after 100 seconds, aborting tests.")

    client = AdminClient(conf)
    topic_ready = False

    n_polls = 0
    while n_polls < 10 and not topic_ready:
        if "TEST_forwarderConfig" in client.list_topics().topics.keys():
            topic_ready = True
            print("Topic is ready!", flush=True)
            break
        sleep(6)
        n_polls += 1

    if not topic_ready:
        docker_cmd.down(docker_options)  # Bring down containers cleanly
        raise Exception("Kafka topic was not ready after 60 seconds, aborting tests.")


common_options = {
    "--no-deps": False,
    "--always-recreate-deps": False,
    "--scale": "",
    "--abort-on-container-exit": False,
    "SERVICE": "",
    "--remove-orphans": False,
    "--no-recreate": True,
    "--force-recreate": False,
    "--no-build": False,
    "--no-color": False,
    "--rmi": "none",
    "--volumes": True,  # Remove volumes when docker-compose down (don't persist kafka and zk data)
    "--follow": False,
    "--timestamps": False,
    "--tail": "all",
    "--detach": True,
    "--build": False,
}


def run_containers(cmd, options):
    print("Running docker-compose up", flush=True)
    cmd.up(options)
    print("\nFinished docker-compose up\n", flush=True)


def build_and_run(options, request):
    project = project_from_options(os.path.dirname(__file__), options)
    cmd = TopLevelCommand(project)
    run_containers(cmd, options)

    start_time = str(int(unix_time_milliseconds(datetime.utcnow())))

    def fin():
        # Stop the containers then remove them and their volumes (--volumes option)
        print("containers stopping", flush=True)
        log_options = dict(options)
        cmd.logs(log_options)
        options["--timeout"] = 30
        cmd.down(options)
        print("containers stopped", flush=True)

    # Using a finalizer rather than yield in the fixture means
    # that the containers will be brought down even if tests fail
    request.addfinalizer(fin)

    return start_time


@pytest.fixture(scope="session", autouse=True)
def remove_logs_from_previous_run(request):
    print("Removing previous log files", flush=True)
    dir_name = os.path.join(os.getcwd(), "logs")
    dirlist = os.listdir(dir_name)
    for filename in dirlist:
        if filename.endswith(".log"):
            os.remove(os.path.join(dir_name, filename))
    print("Removed previous log files", flush=True)


@pytest.fixture(scope="session", autouse=True)
def start_kafka(request):
    print("Starting zookeeper and kafka", flush=True)
    options = common_options
    options["--project-name"] = "kafka"
    options["--file"] = [os.path.join("compose", "docker-compose-kafka.yml")]
    project = project_from_options(os.path.dirname(__file__), options)
    cmd = TopLevelCommand(project)

    cmd.up(options)
    print("Started kafka containers", flush=True)
    wait_until_kafka_ready(cmd, options)

    def fin():
        print("Stopping zookeeper and kafka", flush=True)
        options["--timeout"] = 30
        options["--project-name"] = "kafka"
        options["--file"] = [os.path.join("compose", "docker-compose-kafka.yml")]
        cmd.down(options)

    request.addfinalizer(fin)


@pytest.fixture(scope="module", autouse=False)
def start_ioc(request):
    options = common_options
    options["--project-name"] = "ioc"
    options["--file"] = [os.path.join("compose", "docker-compose-ioc.yml")]
    project = project_from_options(os.path.dirname(__file__), options)
    cmd = TopLevelCommand(project)

    cmd.up(options)

    def fin():
        print("Stopping zookeeper and kafka", flush=True)
        options["--timeout"] = 30
        options["--project-name"] = "ioc"
        options["--file"] = [os.path.join("compose", "docker-compose-ioc.yml")]
        cmd.down(options)

    request.addfinalizer(fin)


# Forwarder tests
@pytest.fixture(scope="module")
def docker_compose(request):
    """
    :type request: _pytest.python.FixtureRequest
    """
    print("Started preparing test environment...", flush=True)

    # Options must be given as long form
    options = common_options
    options["--project-name"] = "forwarder"
    options["--file"] = [
        os.path.join("forwarder_tests", "compose", "docker-compose.yml")
    ]

    build_and_run(options, request)


@pytest.fixture(scope="module")
def docker_compose_no_command(request):
    """
    :type request: _pytest.python.FixtureRequest
    """
    print("Started preparing test environment...", flush=True)

    # Options must be given as long form
    options = common_options
    options["--project-name"] = "forwarderNoCommand"
    options["--file"] = [
        os.path.join("forwarder_tests", "compose", "docker-compose-no-command.yml")
    ]

    build_and_run(options, request)


@pytest.fixture(scope="module")
def docker_compose_fake_epics(request):
    """
    :type request: _pytest.python.FixtureRequest
    """
    print("Started preparing test environment...", flush=True)

    # Options must be given as long form
    options = common_options
    options["--project-name"] = "fake"
    options["--file"] = [
        os.path.join("forwarder_tests", "compose", "docker-compose-fake-epics.yml")
    ]

    build_and_run(options, request)


@pytest.fixture(scope="module")
def docker_compose_idle_updates(request):
    """
    :type request: _pytest.python.FixtureRequest
    """
    print("Started preparing test environment...", flush=True)

    # Options must be given as long form
    options = common_options
    options["--project-name"] = "idle"
    options["--file"] = [
        os.path.join("forwarder_tests", "compose", "docker-compose-idle-updates.yml")
    ]

    build_and_run(options, request)


@pytest.fixture(scope="module")
def docker_compose_idle_updates_long_period(request):
    """
    :type request: _pytest.python.FixtureRequest
    """
    print("Started preparing test environment...", flush=True)

    # Options must be given as long form
    options = common_options
    options["--project-name"] = "longi"
    options["--file"] = [
        os.path.join(
            "forwarder_tests", "compose", "docker-compose-idle-updates-long-period.yml"
        )
    ]

    build_and_run(options, request)


@pytest.fixture(scope="module", autouse=False)
def docker_compose_lr(request):
    """
    :type request: _pytest.python.FixtureRequest
    """
    print("Started preparing test environment...", flush=True)

    # Options must be given as long form
    options = common_options
    options["--project-name"] = "lr"
    options["--file"] = [
        os.path.join("forwarder_tests", "compose", "docker-compose-long-running.yml")
    ]

    build_and_run(options, request)


# File-writer tests


@pytest.fixture(scope="module")
def docker_compose_fw(request):
    """
    :type request: _pytest.python.FixtureRequest
    """
    print("Started preparing test environment...", flush=True)

    # Options must be given as long form
    options = common_options
    options["--file"] = [
        os.path.join("filewriter_tests", "compose", "docker-compose.yml")
    ]
    return build_and_run(options, request)


@pytest.fixture(scope="module")
def docker_compose_multiple_instances(request):
    """
    :type request: _pytest.python.FixtureRequest
    """
    print("Started preparing test environment...", flush=True)

    # Options must be given as long form
    options = common_options
    options["--file"] = [
        os.path.join(
            "filewriter_tests", "compose", "docker-compose-multiple-instances.yml"
        )
    ]
    return build_and_run(options, request)


@pytest.fixture(scope="module")
def docker_compose_stop_command(request):
    """
    :type request: _pytest.python.FixtureRequest
    """
    print("Started preparing test environment...", flush=True)
    options = common_options
    options["--file"] = [
        os.path.join("filewriter_tests", "compose", "docker-compose-stop-command.yml")
    ]
    return build_and_run(options, request)


@pytest.fixture(scope="module")
def docker_compose_static_data(request):
    """
    :type request: _pytest.python.FixtureRequest
    """
    print("Started preparing test environment...", flush=True)
    # Options must be given as long form
    options = common_options
    options["--file"] = [
        os.path.join("filewriter_tests", "compose", "docker-compose-static-data.yml")
    ]
    return build_and_run(options, request)


@pytest.fixture(scope="module", autouse=False)
def docker_compose_long_running(request):
    """
    :type request: _pytest.python.FixtureRequest
    """
    print("Started preparing test environment...", flush=True)
    # Options must be given as long form
    options = common_options
    options["--file"] = [
        os.path.join("filewriter_tests", "compose", "docker-compose-lr.yml")
    ]
    return build_and_run(options, request)


# SQL tests


@pytest.fixture(scope="module", autouse=False)
def docker_compose_sql(request):
    options = common_options
    options["--file"] = [os.path.join("compose", "docker-compose-sql.yml")]
    return build_and_run(options, request)
