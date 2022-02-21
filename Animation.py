import math
import threading
import time
import inputs
from inputs import devices
from adafruit_servokit import ServoKit
# from mock import MagicMock
# ServoKit = MagicMock()

SERVO_COUNT = 16  # max of 16 due to PCA9685 board
_servoKit = ServoKit(channels=SERVO_COUNT)

# TODO
# class AnamatronicView:
#     # Contains 2 eyes (including eyelids) Each servo should/could be constrained
#     # Contains 1 mouth (still dont know what that looks like yet)


def map(input, in_min, in_max, out_min, out_max):
    in_min = 1.0 * in_min
    return (input - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def constrain(input, min, max):
    if input < min:
        return min
    elif input > max:
        return max
    else:
        return input


class Servo:
    def __init__(self, id, min=0, max=180, starting=90):
        self.Id = id
        self.Min = min
        self.Max = max
        self.Starting = starting
        self.Angle = self.Starting

    def set(self, angle=None):
        if angle is None:
            angle = self.Starting

        self.Angle = constrain(angle, self.Min, self.Max)
        # TODO this should not be happening in this class.
        # This class should only be a DTO class and should not do the work
        _servoKit.servo[self.Id].angle = self.Angle


# TODO this class needs a config file for min and max values on servos and
#  perhaps a program that builds that config file for you?
class Eye:
    def __init__(self, config):
        self._name = config['Name']
        self._servoX = Servo(**config['X_Servo'])
        self._servoY = Servo(**config['Y_Servo'])
        self._servoE = Servo(**config['E_Servo'])
        self._servos = [self._servoX, self._servoY, self._servoE]

        init_delay = 1
        print(f'{self._name}: Setting servos to min values')
        [servo.set(servo.Min) for servo in self._servos]
        time.sleep(init_delay)

        print(f'{self._name}: Setting servos to max values')
        [servo.set(servo.Max) for servo in self._servos]
        time.sleep(init_delay)

        print(f'{self._name}: Setting servos to starting values')
        [servo.set(servo.Starting) for servo in self._servos]
        time.sleep(init_delay)

    def reset(self):
        self._servoX.set()
        self._servoY.set()
        self._servoE.set()

    def update(self, x, y, rt, **kwargs):
        self._servoX.set(map(x, -1, 1, 0, 180))
        self._servoY.set(map(y, 1, -1, 0, 180))
        self._servoE.set(map(rt, 0, 1, 0, 90))


class XboxController(object):
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):
        self._setup = False
        if len(devices.gamepads) == 0:
            print('No gamepad detected skipping controller setup')
            return

        self._setup = True
        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

        self._monitor_thread = threading.Thread(target=self._update_values, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def read(self):
        x_joy = round(self.LeftJoystickX, 2)
        y_joy = round(self.LeftJoystickY, 2)
        rt = round(self.RightTrigger, 2)
        a = self.A
        b = self.B
        x = self.X
        y = self.Y
        back = self.Back
        return {
            'x_joy': x_joy,
            'y_joy': y_joy,
            'rt': rt,
            'back': back,
            'rb': self.RightBumper,
            'lb': self.LeftBumper,
            'a': a,
            'b': b,
            'x': x,
            'y': y}

    # for some reason on windows back and select are wrong
    def _update_values(self):
        while True:
            events = inputs.get_gamepad()
            for event in events:
                if event.code == 'ABS_Y':
                    self.LeftJoystickY = event.state / XboxController.MAX_JOY_VAL  # map between -1 and 1
                elif event.code == 'ABS_X':
                    self.LeftJoystickX = event.state / XboxController.MAX_JOY_VAL  # map between -1 and 1
                elif event.code == 'ABS_RY':
                    self.RightJoystickY = event.state / XboxController.MAX_JOY_VAL  # map between -1 and 1
                elif event.code == 'ABS_RX':
                    self.RightJoystickX = event.state / XboxController.MAX_JOY_VAL  # map between -1 and 1
                elif event.code == 'ABS_Z':
                    self.LeftTrigger = event.state / XboxController.MAX_TRIG_VAL  # map between 0 and 1
                elif event.code == 'ABS_RZ':
                    self.RightTrigger = event.state / XboxController.MAX_TRIG_VAL  # map between 0 and 1
                elif event.code == 'BTN_TL':
                    self.LeftBumper = event.state
                elif event.code == 'BTN_TR':
                    self.RightBumper = event.state
                elif event.code == 'BTN_SOUTH':
                    self.A = event.state
                elif event.code == 'BTN_NORTH':
                    self.X = event.state
                elif event.code == 'BTN_WEST':
                    self.Y = event.state
                elif event.code == 'BTN_EAST':
                    self.B = event.state
                elif event.code == 'BTN_THUMBL':
                    self.LeftThumb = event.state
                elif event.code == 'BTN_THUMBR':
                    self.RightThumb = event.state
                elif event.code == 'BTN_SELECT':
                    self.Back = event.state
                elif event.code == 'BTN_START':
                    self.Start = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY1':
                    self.LeftDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY2':
                    self.RightDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY3':
                    self.UpDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY4':
                    self.DownDPad = event.state

    def view_controller_input(self):
        print('Debug: viewing controller input. Press back (select on windows) to return')
        while self.Back == 0:
            msg = (f'LT: {self.LeftTrigger:.2f}, '
                   f'LB: {self.LeftBumper}, '
                   f'RT: {self.RightTrigger:.2f}, '
                   f'RB: {self.RightBumper}, '
                   f'back:{self.Back}, '
                   f'start:{self.Start}, '
                   f'x:{self.X}, '
                   f'y:{self.Y}, '
                   f'b:{self.B}, '
                   f'a:{self.A}, '
                   f'LJoy ({self.LeftJoystickX:.2f},{self.LeftJoystickY:.2f}), '
                   f'RJoy ({self.RightJoystickX:.2f},{self.RightJoystickY:.2f})')
            print(msg, end='\r')
        print('')


if __name__ == '__main__':
    joy = XboxController()
    joy.view_controller_input()

    left_eye_config = {
        'Name': 'Left Eye',
        'X_Servo': {
            'id': 0,
            'min': 30,
            'max': 150,
            'starting': 90
        },
        'Y_Servo': {
            'id': 1,
            'min': 30,
            'max': 150,
            'starting': 90
        },
        'E_Servo': {
            'id': 2,
            'min': 0,
            'max': 130,
            'starting': 0
        }
    }
    left_eye = Eye(left_eye_config)

    right_eye_config = {
        'Name': 'Right Eye',
        'X_Servo': {
            'id': 3,
            'min': 30,
            'max': 150,
            'starting': 90
        },
        'Y_Servo': {
            'id': 4,
            'min': 30,
            'max': 150,
            'starting': 90
        },
        'E_Servo': {
            'id': 5,
            'min': 0,
            'max': 95,
            'starting': 0
        }
    }
    right_eye = Eye(right_eye_config)

    print('Discover Limits')
    while True:
        input_set = joy.read()
        left_eye._servoY.set(left_eye._servoY.Angle + (5 * int(input_set['y'])))
        left_eye._servoY.set(left_eye._servoY.Angle - (5 * int(input_set['a'])))
        right_eye._servoY.set(left_eye._servoY.Angle + (5 * int(input_set['y'])))
        right_eye._servoY.set(left_eye._servoY.Angle - (5 * int(input_set['a'])))

        left_eye._servoX.set(left_eye._servoX.Angle + (5 * int(input_set['x'])))
        left_eye._servoX.set(left_eye._servoX.Angle - (5 * int(input_set['b'])))
        right_eye._servoX.set(left_eye._servoX.Angle + (5 * int(input_set['x'])))
        right_eye._servoX.set(left_eye._servoX.Angle - (5 * int(input_set['b'])))

        left_eye._servoE.set(left_eye._servoE.Angle + (5 * int(input_set['rb'])))
        left_eye._servoE.set(left_eye._servoE.Angle - (5 * int(input_set['lb'])))
        right_eye._servoE.set(left_eye._servoE.Angle + (5 * int(input_set['rb'])))
        right_eye._servoE.set(left_eye._servoE.Angle - (5 * int(input_set['lb'])))
        print(f'X servo Angle = {left_eye._servoX.Angle:3}  ' +
              f'Y servo Angle = {left_eye._servoY.Angle:3}  ' +
              f'E servo Angle = {left_eye._servoE.Angle:3} {input_set}', end='\r')
        time.sleep(.1)
        if input_set['back']:
            print('')
            break

    print('Passthrough Playback')
    while True:
        input_set = joy.read()
        print(input_set, end='     \r')
        if input_set['back'] == 1:
            print('')
            break

        x_val = input_set['x_joy']
        x_val = map(x_val, -1, 1, left_eye._servoX.Min, left_eye._servoX.Max)
        left_eye._servoX.set(x_val)
        right_eye._servoX.set(x_val)

        y_val = input_set['y_joy']
        y_val = map(y_val, 1, -1, left_eye._servoY.Min, left_eye._servoY.Max)
        left_eye._servoY.set(y_val)
        right_eye._servoY.set(y_val)

        eyelid = input_set['rt']
        left_eyelid = map(eyelid, 0, 1, left_eye._servoE.Min, left_eye._servoE.Max)
        right_eyelid = map(eyelid, 0, 1, right_eye._servoE.Min, right_eye._servoE.Max)
        left_eye._servoE.set(left_eyelid)
        right_eye._servoE.set(right_eyelid)

    left_eye.reset()
    right_eye.reset()

    print('')
    print('Thanks for playing')
