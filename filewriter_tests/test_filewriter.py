import os

import pytest

from helpers.kafka_helpers import create_producer, send_writer_command
from helpers.nexushelpers import OpenNexusFileWhenAvailable
from time import sleep
import numpy as np


@pytest.mark.skip(reason="Broken for some reason")
def test_data_reaches_file(docker_compose_fw):
    producer = create_producer()
    sleep(20)
    # Start file writing
    send_writer_command(
        os.path.join("filewriter_tests", "commands", "example-json-command.json"),
        producer,
        start_time=docker_compose_fw,
    )
    producer.flush()
    # Give it some time to accumulate data
    sleep(10)
    # Stop file writing
    send_writer_command(
        os.path.join("filewriter_tests", "commands", "stop-command.json"), producer
    )
    sleep(10)
    send_writer_command(
        os.path.join("filewriter_tests", "commands", "writer-exit.json"), producer
    )
    producer.flush()

    filepath = os.path.join("filewriter_tests", "output-files", "output_file.nxs")
    with OpenNexusFileWhenAvailable(filepath) as file:
        # Static checks
        assert not file.swmr_mode
        assert file["entry/start_time"][...] == "2016-04-12T02:58:52"
        assert file["entry/end_time"][...] == "2016-04-12T03:29:11"
        assert file["entry/duration"][...] == 1817.0
        assert file["entry/features"][0] == 10138143369737381149
        assert file["entry/user_1/affiliation"][...] == "ISIS, STFC"
        assert np.allclose(
            file["entry/instrument/monitor1/transformations/location"].attrs["vector"],
            np.array([0.0, 0.0, -1.0]),
        )
        assert (
            file["entry/instrument/monitor1/transformations/location"].attrs[
                "transformation_type"
            ]
            == "translation"
        )

        # Streamed checks
        # Ev42 event data (Detector_1)
        assert file["entry/detector_1_events/event_id"][0] == 99406
        assert file["entry/detector_1_events/event_id"][1] == 98345
        # f142 Sample env (Sample)
        assert np.isclose(
            21.0, file["entry/sample/sample_env_logs/Det_Temp_RRB/value"][0]
        )
