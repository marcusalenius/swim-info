'''
This file contains the ProgressBar class that can be used to display a progress
bar in the terminal. 
'''

class ProgressBar:
    def __init__(self, bar_length: int) -> None:
        '''
        Initializes a ProgressBar object with the given bar length. The bar
        length is the number of characters the bar will be displayed with. It 
        must be greater than 0. Calls the _draw method to display the empty
        progress bar.
        '''
        assert bar_length > 0, 'Bar length must be greater than 0.'
        self.bar_length = bar_length
        self.num_events = None
        self.curr_event = 0
        self.num_heats = None
        self.curr_heat = 0
        self._draw(0)
    
    def set_num_events(self, num_events: int) -> None:
        '''
        Sets the number of events. It must be greater than 0.
        '''
        assert num_events > 0, 'Number of events must be greater than 0.'
        self.num_events = num_events
    
    def update_event(self, event: int) -> None:
        '''
        Updates the current event number. The event number must be greater than
        0 and less than or equal to the number of events.
        '''
        assert 0 < event <= self.num_events, 'Event number must be in range.'
        self.curr_event = event
        self.curr_heat = 1

    def set_num_heats(self, num_heats: int) -> None:
        '''
        Sets the number of heats. It must be greater than 0.
        '''
        assert num_heats > 0, 'Number of heats must be greater than 0.'
        self.num_heats = num_heats

    def update_heat(self, heat: int) -> None:
        '''
        Updates the current heat number. The heat number must be greater than 0
        and less than or equal to the number of heats. Calls the _draw method
        to display the updated bar.
        '''
        assert 0 < heat <= self.num_heats, 'Heat number must be in range.'
        self.curr_heat = heat
        event_filled_up_length = self.bar_length * (self.curr_event / 
                                                    self.num_events)
        one_event_length = self.bar_length / self.num_events
        heat_filled_up_length = one_event_length * (self.curr_heat / 
                                                    self.num_heats)
        filled_up_length = event_filled_up_length + heat_filled_up_length
        self._draw(filled_up_length)

    def _draw(self, filled_up_length: float) -> None:
        '''
        Internal method to draw the progress bar with the given filled up 
        length.
        '''
        percentage = round(100 * filled_up_length / self.bar_length, 1)
        filled_up_length = int(filled_up_length)
        bar = ("#" * filled_up_length + 
               "." * (self.bar_length - filled_up_length))
        print(f'[{bar}] {percentage}%', end='\r')
        if percentage == 100:
            print()
