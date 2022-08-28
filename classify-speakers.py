#!/usr/bin/env python
"""Filters the speakers of crawled sessions into Parliament members and guests."""
from argparse import ArgumentParser
from utils.loggingutils import configure_logging
from pathlib import Path
import logging
import json
import csv
import pandas as pd


def save_data_frame(data_frame, file_name):
    """Save the provided data frame into specified CSV file.

    Parameters
    ----------
    data_frame: pandas.DataFrame, required
        The data frame to save.
    file_name: str, required
        The path of the CSV file where to save the data frame.
    """
    output_file = Path(file_name)
    if not output_file.parent.exists():
        output_file.parent.mkdir(parents=True, exist_ok=True)
    data_frame.to_csv(file_name, quoting=csv.QUOTE_NONNUMERIC)


def load_speakers(sessions_directory):
    """Parse sessions in the specified directory and load all speakers.

    Parameters
    ----------
    sessions_directory: str, required
        The directory containing the JSON files with session transcripts.

    Returns
    -------
    speakers: list of dict
        The list of all speakers from all sessions.
    """
    speakers = []
    for f in Path(sessions_directory).glob("*.json"):
        logging.info("Reading speakers from %s.", f)
        with open(str(f), 'r', encoding='utf8') as input_file:
            session = json.load(input_file)
            if 'sections' not in session:
                logging.error("Could not find session sections in %s.", f)
                continue

            for section in session['sections']:
                speaker = section['speaker']
                contents = section['contents']
                if contents is None or len(contents) == 0:
                    continue
                if speaker is None:
                    logging.warning("Found null speaker in section %s.",
                                    section)
                    continue

                speakers.append(speaker)

    return speakers


def is_guest(speaker):
    """Determine whether the provided speaker is a guest or a member of the Parliament.

    Parameters
    ----------
    speaker: dict, required
        The speaker.

    Returns
    -------
    is_guest: bool
        True if the speaker is a guest; False if the speaker is a member of the Parliament.
    """
    profile_url = speaker['profile_url']
    return profile_url is None or len(profile_url) == 0


def main(args):
    """Filter speakers into Parliament members and guests."""
    guests, members = {}, {}
    for speaker in load_speakers(args.sessions_dir):
        speaker_name = speaker['full_name']
        guest_speaker = is_guest(speaker)
        if guest_speaker and speaker_name not in guests:
            guests[speaker_name] = speaker
        if (not guest_speaker) and (speaker_name not in members):
            members[speaker_name] = speaker

    guests = list(guests.values())
    members = list(members.values())
    save_data_frame(pd.DataFrame.from_records(guests), args.guests_file)
    save_data_frame(pd.DataFrame.from_records(members), args.members_file)
    logging.info("That's all folks!")


def parse_arguments():
    """Parse the command-line arguments.

    Returns
    -------
    args: argparse.Namespace
        The command-line arguments.
    """
    parser = ArgumentParser(description='Filter speakers of crawled sessions.')
    parser.add_argument(
        '--sessions-dir',
        help="The path of the directory containing crawled sessions.",
        type=str,
        default="./data/sessions/")
    parser.add_argument(
        '--save-members-to',
        help="The path of the output CSV file containing speakers.",
        type=str,
        dest='members_file',
        default="./data/speakers/parliament-members.csv")
    parser.add_argument(
        '--save-guests-to',
        help="The path of the output CSV file containing speakers.",
        type=str,
        dest='guests_file',
        default="./data/speakers/guest-speakers.csv")
    parser.add_argument(
        '-l',
        '--log-level',
        help="The level of details to print when running.",
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='info')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    configure_logging(args.log_level)
    main(args)
