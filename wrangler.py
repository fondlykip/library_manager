import argparse
import json
import logging
from pathlib import Path
from src.helpers import file_helpers as f_help
from src.helpers import user_io
from src.helpers import library_utils
from src.config import SYS_VARS, USER_VARS, config_utils


def start_up():
    """Function to run various start up logic
    on starting the app.
    Args:
        None
    Returns:
        True: success mode
    """
    logging.info(f"Hello, {USER_VARS['USER_NAME']}")
    logging.debug(f"Application started")
    return True


def teardown_process():
    """Function to run various teardown processes after app
    has finished running
    Args:
        None
    Returns:
        True: Success Mode
        False: Failure Mode
    """
    session_end = config_utils.teardown()
    logging.info(f"session ended: {session_end}")
    logging.info(f"GOODBYE CRUEL WORLD 👋")
    return True


def unzip(arg_parser: argparse.ArgumentParser,
          args: argparse.Namespace):
    input_path_str = args.input_folder
    while not f_help.validate_path(input_path_str, True):
        default = USER_VARS.get('DEFAULT_INPUT_FOLDER', None)
        input_path_str = user_io.prompt_for_variable("input path", default)
    
    input_path = Path(input_path_str)
    
    output_path_str = args.output_folder
    if output_path_str:   
        while not f_help.validate_path(output_path_str, False):
            default = USER_VARS.get('DEFAULT_OUTPUT_FOLDER', None)
            output_path_str = user_io.prompt_for_variable("output path", default)

        output_path = Path(output_path_str)
        if input_path.is_dir():
            return f_help.bulk_extract(input_path, output_path)

    elif user_io.prompt_user_Yn("Proceed to unzip files in the same location?"):
        if input_path.is_dir():
            return f_help.bulk_extract(input_path)

        if input_path.exists():
            return f_help.extract_file(input_path)


def balance(parser,
            args: argparse.Namespace):
    gt_path = args.gt_path
    ch_path = args.ch_path
    if not (type_list := args.types_list):
        type_list = USER_VARS['DEFAULT_TYPES']

    gt_files = f_help.get_files(
                            gt_path,
                            type_list,
                            True
                        )
    ch_files = f_help.get_files(
                            ch_path,
                            type_list,
                            True
                        )

    

def vars(parser,
         args:argparse.Namespace):
    if not args.show and not args.update:
        parser.print_help()
        args.show = user_io.prompt_user_Yn("Would you like to see the current set Variables?")
        args.update = user_io.prompt_user_Yn("Would you like to update one?")

    if args.show or args.upd:
        config_utils.show_vars()
    
    
    if args.update:
        key_to_update = user_io.prompt_for_choice(USER_VARS.keys())
        current = USER_VARS[key_to_update]
        value_to_insert = user_io.prompt_for_variable(
                                        var_name=key_to_update,
                                        default=current)
        config_utils.set_var(key_to_update, value_to_insert)
        config_utils.save_vars()



def refile(parser, args: argparse.Namespace):
    target = args.target
    if target is None or not isinstance(target, str):
        target = user_io.prompt_for_variable("target path", target)

    target_path = Path(target)
    
    dest_path = Path(args.destination)
    f_help.clean_folder(
                target_path,
                output_folder = None,
                dry_run=args.dry_run
            )
    pass
    



if __name__ == "__main__":
    log_id = f"{__file__}.main_process"
    pname = SYS_VARS['PNAME']
    pusage = SYS_VARS['PUSAGE']

    # Add Baseline args
    arg_parser = argparse.ArgumentParser(prog=pname,
                                         usage=pusage)
    arg_parser.add_argument(
        "--debug",
        action="store_true",
        help="""
            Flag parameter used to view debug logs
            of the script to help find issues.
        """
    )
    subpars = arg_parser.add_subparsers(
        dest="command"
    )

    # Add common Args between file wrangling commands
    parser_super = argparse.ArgumentParser(add_help=False)
    parser_super.add_argument(
        "-i", "--input-folder",
        default=USER_VARS.get('DEFAULT_INPUT_FOLDER', None),
        help="""
            Used to set the input folder where the helper
            can find the bandcamp files in need of
            formatting.
        """
    )
    parser_super.add_argument(
        "-o", "--output-folder",
        default=USER_VARS.get('DEFAULT_OUTPUT_FOLDER', None),
        help="""
            Used to set the output folder where the 
            wrangler will send the resulting files to.
        """
    )

    # subparser for vars command
    vars_sp = subpars.add_parser(
        "vars", 
        help="Initialise the application"
    )
    vars_sp.add_argument(
        "-s", "--show",
        help="""
            Take a look at currently assigned
            variables
        """
    )
    vars_sp.add_argument(
        "-u", "--update",
        help="""
            Do you want 
        """
    )

    # subparser for init command
    init_sp = subpars.add_parser(
        "init", 
        help="Initialise the application"
    )

    # subparser for unzip command
    unzip_sp = subpars.add_parser(
        "unzip", 
        help="Unzip bandcamp files",
        usage="Submodule used to unzip batches of bandcamp files",
        parents=[parser_super]
    )
    unzip_sp.add_argument(
        "-m", "--move-parsed",
        help="move processed zip files to new location",
        action="store_true"
    )

    # subparser for balance command
    balance_sp = subpars.add_parser(
        "balance", 
        help="bring balance back to two directories.",
        usage="Submodule used to balance pairs of file sets",
    )
    balance_sp.add_argument(
        "-t", "--types-list",
        action="append",
        help="""
                target specific file_types for the rebalancing. \n
                eg: `-t aiff -t wav -t mp3 -t m4a` etc.
            """
    )
    balance_sp.add_argument(
        "-g", "--gt-path",
        help="""
            The path to the dir considered to be the
            ground truth against which the other dir
            will be checked
        """,
        required=True
    )
    balance_sp.add_argument(
        "-c", "--ch-path",
        help="""
            The path to be checked against the ground
            truth for any sign of misalign ment
        """,
        required=True
    )

    # subparser for refile command
    refile_sp = subpars.add_parser(
        "refile",
        help="Submodule to refile the bandcamp files"
    )
    refile_sp.add_argument(
        "-t", "--target",
        help="""The target folder which we want to
                refile to iTunes standard""",
        required=True
    )
    refile_sp.add_argument(
        "-d", "--destination",
        help="""The destination folder in which we will
                refile the existing files"""
    )
    refile_sp.add_argument(
        "--dry-run",
        action="store_true",
        help="""
            Log the proposed changes with out making any
            changes to the files
        """
    )

    # subparser for refile command
    itunes_sp = subpars.add_parser(
        "itunes",
        help="Submodule to process itunes files",
        parents=[parser_super]
    )


    args = arg_parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")

    if SYS_VARS['FIRST_RUN'] or args.command=="init":
        set_vars = config_utils.user_setup(True)
        logging.info(f"""{log_id} | Successfully set user variables:
                        {json.dumps(set_vars, indent=4, default=str)}
                     """)

    _ = start_up()

    exec_dict = {
        'unzip': unzip,
        'balance': balance,
        'vars': vars,
        'refile': refile
    }
    logging.info(f"{log_id} | Running {args.command}")
    try:
        result = exec_dict[args.command](arg_parser, args)
    except KeyError:
        logging.error(f"it looks like the requested feature isn't here yet, awwwwww too bad.")


    _ = teardown_process()
    