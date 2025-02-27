import logging


def prompt_for_choice(options: list):
    log_id = f"{__name__}.prompt_for_choice"
    if len(options) == 0 or not options:
        logging.info(f"{log_id} | No options supplied for user: {options}")
        raise Exception("Whoopsie!")

    print("please select from the following options:")
    for i, opt in enumerate(options):
        print(f"[{i}] - {opt}")

    while True:
        sel = input(f"your selection [0-{len(options)-1}]:")
        try:
            int_sel = int(sel)
            if (0 <= int_sel < len(options)):
                return options[int_sel]

            print(f"your selection must be within the specfified range [0-{len(options)-1}]")

        except ValueError as e:
            print(f"Your selection must be a valid number from the supplied range")


def prompt_for_variable(var_name: str, default = None):
    while True:
        resp = input(f"Please provide a(n) {var_name} ({default}): ")
        if default and len(resp) == 0:
            if prompt_user_Yn(f"keep default value {default}?"):
                return default
        elif resp and len(resp) > 0:
            return resp


def prompt_user_Yn(question: str):
    valid_choice = False
    while not valid_choice:
        resp = input(question)
        if resp.lower() in ['y', 'yes']:
            return True
        elif resp.lower() in ['n', 'no']:
            return False
        else:
            print("please provide answer from y/yes/Y/YES or n/N/no/NO")