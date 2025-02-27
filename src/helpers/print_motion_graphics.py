import time


class motionGraphics:
    """A Class implementing some fun custom print functionality"""
    def __init__(self, 
                 frame_rate: int = 0.1, 
                 replace_last:bool = True,
                 new_lines: bool = False,
                 flush: bool = True,
                 starting_state: str = None):
        self.frame_rate = frame_rate
        self.replace_last = replace_last
        self.new_lines = new_lines
        self.flush = flush
        self.state = ''
        if starting_state:
            self.state = starting_state


    def set_state(self, state):
        """
        Add a new state to the global config.
        Args:
            state (any): New state to add to global config.
        """
        self.state = str(state)
        return self.state


    def set_frame_rate(self, new_rate):
        """
        A function to set the global config frame rate.
        Args:
            new_rate (int | float): New frame rate to set in global config.
        """
        if not (type(new_rate) == int or type(new_rate) == float):
            raise Exception("Frame rates must be in a number format - int or float")
        self.frame_rate = new_rate
    
    
    def _determine_state(self, word: str, use_state: bool):
        """
        Function to set new state, or use existing state, based
        on user input to caller.
        Args:
            word (str): proposed replacement for state
            use_state (bool): whether user wants to use exisiting state
        """
        if not word and not use_state:
            raise Exception(
                "No word provided - must use saved state or provide word"
            )
        elif use_state and not word:
            word = self.state
        return word


    def cust_print(self, statement):
        """
        A wrapper around default python print statement to
        print according to defined user config for new lines
        Args:
            statement (str): statement to print
        """
        if self.replace_last:
            statement = "\r"+str(statement)
        if not self.new_lines:
            end = ""
        else:
            end = "\n"
        print(statement, end=end, flush=self.flush)
        self.state = statement


    def hold_n_frames(self, num_frames: int):
        """
        A Function to hold for a specified amount of Frames.
        Uses `time.sleep()` to sleep for the input number of frames
        multiplied by the class config frame_rate variable
        Args:
            num_frames (int): num of frames to hold the
        """
        time.sleep(self.frame_rate * num_frames)


    def _replace_char_at_index(self,
                               replace_in: str,
                               replace_with:str,
                               index: int)-> str:
        """
        A Function to replace a character at a given index in a string
        Args:
            replace_in (str): word to replace the char in
            replace_with (str): character to replace char at index with
            index (str): index to replace character at
        Returns:
            updated_str (str): string with char at index replaced with input
        """
        if index < 0 or index>=len(replace_in):
            raise IndexError(
                f"Index to replace {index} is out of bounds for input {replace_in}"
            )
        return replace_in[:index] + replace_with + replace_in[index+1:]


    def type_word(self,
                  word: str):
        """
        Function to print out a given word one character at a time.
        Arg:
            word (str): string to print out
        """
        word = word.center(len(self.state)+1)
        state = ''
        for char in list(word):
            state += char
            self.cust_print(state)
            time.sleep(self.frame_rate)
        self.state = state


    def mask_word(self, 
                  word: str = None, 
                  masking_char:str='#',
                  save_state:bool = True,
                  use_state:bool = True):
        """
        Function to mask a given word or the global state,
        one char at a time, using a given masking_char (# by default)
        Arg:
            word (str): string to mask
            masking_char (str): char to use for masking
            save_state (bool, optional): whether to save the state at the
                                         end of this operation to the global class level
                                         config (default True)
            use_state (bool, optional): Whether to use the class level 
                                        saved state for this operation.
        """
        state = self._determine_state(word, use_state)
        for i in range(0, len(state)):
            state = self._replace_char_at_index(state, masking_char, i)
            self.cust_print(state)
            time.sleep(self.frame_rate)
        if save_state:
            self.state = state


    def replace_from_outside(self, 
                             word: str = None, 
                             replace_with: str = '-',
                             final_char: str = None,
                             use_state: bool = True):
        """
        A function to replace all characters in previous print 
        with a given character from the outside in. when given
        the final_char variable, it will place this char in the
        middle of the result on the final iteration.
        Args:
            word (str, optional): word to use as basis for this operation. 
                        Can be None if global state is being used
            replace_with (str, optional): str to replace each char 
                                          in the given
                                          word or state with.
            final_char (str, optional): character to place in the middle of the result
                                        at the end
            use_state (bool, optional): Whether to use the class level 
                                        saved state for this operation.
        """
        state = self._determine_state(word, use_state)

        if len(state)%2 == 0:
            its = int(len(state)/2)
        else:
            its = int((len(state)/2) + 1)
        
        self.cust_print(state)
        
        for i in range(0, its):
            state = self._replace_char_at_index(
                    state, replace_with, i
                )
            state = self._replace_char_at_index(
                state, replace_with, (len(state)-(i+1))
            )
            self.cust_print(state)
            time.sleep(self.frame_rate)
        
        # Print the final center char if supplied by user
        if final_char:
            state = f"{state[:i]}{final_char}{state[len(state)-i:]}"
            self.cust_print(state)
            time.sleep(self.frame_rate)
        self.state = state


    def new_line(self):
        """
        Insert a new line in the printed output
        """
        print("", flush=True)

    
    def lock_animation(self):
        """
        A Custom animation using the print tools of this module
        """
        self.replace_from_outside(
            replace_with='-',
            final_char='V'
        )
        self.hold_n_frames(5)
        if len(self.state)%2 == 0:
            update_index = int(len(self.state)/2) + 1
        else:
            update_index = int(len(self.state)/2)
        self.state = self._replace_char_at_index(
            self.state, '>', update_index
        )
        self.cust_print(self.state)
