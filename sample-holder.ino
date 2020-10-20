/**
 * Stepper motor controller for 
 * Spectroscopy Lab (CH G1 521) sample holder
 * 
 * For use with an Arduino Motor Shield,
 * RS 440-420 Bipolar stepping motor
 * 
 * Author: Brian Carlsen
 * Contact: carlsen.bri@gmail.com
 * Date: 04-2019
 */

 /**
  * API
  * 
  * 
  */

#include <Stepper.h>
#include <ArduinoJson.h>

char TERMINATION_CHAR = '\n';

// pin setup
int PWM_A = 3; 
int PWM_B = 11;
int DIR_A = 12; 
int DIR_B = 13; 

int HOME_PWR = 6;
int HOME     = 7;

/*--- unused pins ---
int BRK_A = 9;  // motor brake
int BRK_B = 8;
int CUR_A = 0;  // current sensing, analog pins
int CUR_B = 1; 
----------------------*/

// motor parameters
int STEPS_PER_ROTATION = 200;    // motor steps per revolution
float MOTOR_RPM_DEFAULT = 30.0;  // deafult rotation speed in rpm
float DEGREES_PER_STEP = 360.0/ STEPS_PER_ROTATION;

int motor_position = 0; // current step position of the motor
float motor_speed = MOTOR_RPM_DEFAULT;

// initialize stepper library on direction pins
Stepper motor( STEPS_PER_ROTATION, DIR_A, DIR_B );

void setup() {
  Serial.setTimeout( 5000 );
  Serial.begin( 9600 );

  pinMode( PWM_A, OUTPUT );
  pinMode( PWM_B, OUTPUT );

  pinMode( HOME, INPUT );
  pinMode( HOME_PWR, OUTPUT );
  digitalWrite( HOME_PWR, HIGH );

  disable();
  motor.setSpeed( MOTOR_RPM_DEFAULT );
}

void loop() {
}


void serialEvent() {
  String actionStr = Serial.readStringUntil( TERMINATION_CHAR );
  actionStr.trim();
  
  if ( actionStr == "init" ) {
    Serial.println( actionStr );
  }
  else {
    runAction( actionStr );
  }
}

//--- HELPER FUNCTIONS ---

//--- utilities ---

/**
 * Converts a String to an int.
 * 
 * \param str {String} The String to convert.
 * \param len {int} The number of digits in str. [Default: 10]
 * 
 * \returns {int} The converted String.
 */
int str2int( String str, int len = 10 ) {
  char buff[ len ];
  str.toCharArray( buff, len );
  return atol( buff );
}

/**
 * Converts a String to a float.
 * 
 * \param str {String} The String to convert.
 * \param len {int} The number of digits in str. [Default: 10]
 * 
 * \returns {float} The converted String.
 */
float str2float( String str, int len = 10 ) {
  char buff[ len ];
  str.toCharArray( buff, len );
  return atof( buff );
}

/**
 * Converts a String to a boolean
 * 
 * \param str {String} The String to convert.
 * \returns {bool} Returns true for 'true', false otherwise
 */
bool str2bool( String str ) {
  if ( str == "true" ){
    return true;
  }

  return false;
}
 

/**
 * Writes the given data to the serial port.
 * Ends with a new line character (\n)
 * 
 * \param data {String} The string to print.
 */
void writeData( String data ) {
  Serial.println( data );
}

/**
 * \brief Writes a data array to Serial. 
 * Writes each element in data to the port, separated by <separator>, if given
 * End with a new line character (\n)
 * 
 * \param elms {int} The number of elements from data to print.
 * \param data {char* []} The array of char*'s to print.
 * \param separator {String} A delimeter to separate the elements.
 */
void writeData( int elms, char* data[], String separator = "" ) {
  String str = "";
  for ( int i = 0; i < elms; i++ ) {
    str += separator;
    str += data[ i ];
  }
  str.remove( 0, separator.length() ); // remove initial separator
  
  Serial.println( str ); // print data
}

/**
 * Returns the first index of a value in an array.
 * 
 * \param arr {int []} An array of integers to search
 * \param val {int} The value to search for
 * 
 * \returns {int} The index of the value if found, or -1 if not found
 */
int indexOf( int arr[], int val ) {
  int maxIndex = sizeof( *arr )/ sizeof( arr[ 0 ] );
  for ( int i = 0; i < maxIndex; i++ ) {
    if ( arr[ i ] == val ) {
      return i;
    }
  }

  return -1;
}


/**
 * Converts a motor position into a rotation
 * 
 * \param {int} pos The step position, an integer between 0 and STEPS_PER_ROTATION.
 * \param {bool} rad Return in degrees or radians. [Default: Degrees]
 * 
 * \returns {float} The angular rotation of the given step position, in degrees or radians.
 */
float position_to_rotation( int pos, bool rad ) {
  float rot = pos* DEGREES_PER_STEP;
  rot *= pos; // position in degrees
  
  if ( rad ) {
    // convert to radians
    rot *= PI/ 180;
  }

  return rot;
}

/**
 * Converts a rotation into a motor position.
 * 
 * \param {float} rot The rotation, a float in (-360, 360) or (-2 Pi, 2 Pi).
 * \param {bool} rad Whether the rotation is in radians or degrees. [Default: Degrees]
 * 
 * \returns {int} The step position of the given rotation.
 */
int rotation_to_position( float rot, bool rad ) {
  // normalize to [0, 360) or [0, 2 pi)
  if ( rot < 0 ) {
    if ( rad ) {
      rot += 360;
    }
    else {
      rot += 2.0* PI;
    }
  }

  if ( rad ) {
    // convert to degrees
    rot *= 180/ PI;
  }

  return rot/ DEGREES_PER_STEP;
}


int modular_difference( int a, int b, int mod ) {
  int x = ( b - a )% mod;
  if ( x < 0 ) {
    x += mod;
  }

  // shortest path from a to b
  if ( x < mod/ 2 ) {
    return x;
  }
  else {
    return x - mod;
  }
}

//--- end utilities ---

void enable( bool hold = true ) {
  int val;
  if ( hold == false ) {
    // release hold
    val = LOW; 
  }
  else {
    // set hold
    val = HIGH;
  }

  digitalWrite( PWM_A, val );
  digitalWrite( PWM_B, val );
}

void disable() {
  digitalWrite( PWM_A, LOW );
  digitalWrite( PWM_B, LOW );
}

/**
 * Returns true if both PWM_A and PWM_B pins are HIGH,
 * otherwise false
 */
bool is_enabled() {
  return ( digitalRead( PWM_A ) && digitalRead( PWM_B ) );
}

void motor_step( int steps ) {
  motor.step( steps );
  update_motor_position( steps );
}

void set_home() {
  motor_position = 0;
}

/**
 * Returns whether the home pin is triggered.
 */
bool at_home() {
  int AVG = 7;
  
  int sum = 0;
  for ( int i = 0; i < AVG; ++i ) {
    sum += digitalRead( HOME );  
  }

  if ( sum > AVG/ 2.0 ) {
    return true;
  }
  else {
    return false;
  }
}

/**
 * Scans one revolution for home positions
 */
void scan( int homed[], bool positions = false ) {  
  bool is_home;
  int j = 0;
  for ( int i = 0; i <= STEPS_PER_ROTATION; ++i ) {
    is_home = at_home();
    
    if ( positions ) {
      if ( is_home ) {
        homed[ j ] = i;
        j++;
      }
    }
    else {
      homed[ motor_position ] = int( is_home );
    }
    
    motor_step( 1 );
  }
}


/**
 * Homes the motor using the Reed sensor
 */
void home() {
  int i;
  int homed[ STEPS_PER_ROTATION ];
  for ( i = 0; i < STEPS_PER_ROTATION; i++ ) {
    // initialize homed array
    homed[ i ] = -1;
  }
  scan( homed, true );

  int start,
      diff;
  int min_diff = STEPS_PER_ROTATION;
  for ( i = 0; i < STEPS_PER_ROTATION; i++ ) { 
    if ( homed[ i + 1 ] == -1 ) {
      // end of home positions
      break;
    }
    
    diff = modular_difference( homed[ i ], homed[ i + 1 ], STEPS_PER_ROTATION );
    if ( abs( diff ) > 1 && abs( diff ) < abs( min_diff ) ) {
      start = homed[ i ];
      min_diff = diff;
    }
  }

  // move to new home
  set_position( start );
  motor_step( min_diff/ 2 );
  set_home();
}

void update_motor_position( int steps ) {
  motor_position += steps;
  if ( motor_position < 0 ) {
    motor_position += STEPS_PER_ROTATION;
  }
  
  motor_position %= STEPS_PER_ROTATION;
}


void set_rpm( float rpm ) {
  motor.setSpeed( rpm );
  motor_speed = rpm;
}

float get_rpm() {
  return motor_speed;
}

void set_position( int pos ) {
  motor_step( pos - motor_position );
}

int get_position() {
  return motor_position;
}

void set_rotation( float rot, bool rad = false ) {
  int pos = rotation_to_position( rot, rad );
  set_position( pos );
}

float get_rotation( bool rad = false ) {
  return position_to_rotation( motor_position, rad );
}

/**
 * Parses an action command sent to the controller.
 * 
 * \param action {String} The action command to parse.
 *        Must take the form of run[<command>, <param 1>, ...]
 *        
 * \param elements {String[]} The array in which to store the action elements.
 * 
 * \returns {int} The size number of elements included in the action.
 *          Returns -1 on error.
 */
int parseAction( String action, String elements[] ) {  
  action.trim();
    
  // validate run[ ... ] format
  if ( action.indexOf( "run[" ) != 0 || action.charAt( action.length() -1 ) != ']' ) {
    // invalid
    return -1;
  } 

  // get delimeter positions
  int start = 4; // start of command string, after "run["
  int delimeters[ 20 ];
  int nDels = 0;
  int index;
  do {
    index = action.indexOf( ",", start );
    if ( index != -1 ) {
      // delimeter found
      delimeters[ nDels ] = index; // save position
      start = index + 1; // start from next position
      ++nDels;
    }
  } while( index != -1 );

  // add end of action delimeter
  delimeters[ nDels ] = action.length() - 1;

  // get elements
  String temp;
  start = 4;
  for ( index = 0; index <= nDels; index++ ) { 
    // get substring of element
    temp = action.substring( start, delimeters[ index ] ); 
    temp.trim(); 
    elements[ index ] = temp; 

    // start at next position
    start = delimeters[ index ] + 1; 
  }
  
  return ( nDels + 1 );
}

/**
 * Runs an action command sent to the controller.
 * 
 * \param action {String} The action command to run.
 *        Must take the form of run[<command>, <param 1>, ...]
 */
int runAction( String action ) {
  action.trim();
  String elements[ 10 ];
  int actionSize = parseAction( action, elements );
  String command = elements[ 0 ];
  String response = "";
  boolean success = true;
  int id = -1;

  // commands
   if ( actionSize < 0 ) {
    // invalid
    success = false;
  }
  else if ( command == "termination_char" ) {
    response = TERMINATION_CHAR;
  }
  else if ( command == "echo" && actionSize == 2 ) {
    response = elements[ 1 ];
  }
  else if ( command == "enable" && actionSize < 3 ) {
    if ( actionSize == 1 ) {
       enable();
    }
    else {
      bool hold = str2bool( elements[ 1 ] );
      enable( hold );
    }

    success = true;
  }
  else if ( command == "disable" ) {
    disable();
    success = true;
  }
  else if ( command == "is_enabled" ){
    response = is_enabled();
  }
  else if ( command == "set_home" ) {
    set_home();
    success = true; 
  }
  else if ( command == "set_rpm" && actionSize == 2 ) {
    float rot = str2float( elements[ 1 ] );
    set_rpm( rot );
    success = true;
  }
  else if ( command == "get_spr" || command == "steps_per_rotation" ) {
    id = STEPS_PER_ROTATION;
  }
  else if ( command == "get_pos" || command == "get_position" ) {
    id = get_position();
  }
  else if ( ( command == "get_rot" || command == "get_rotation" ) && actionSize < 3 ) {
    if ( actionSize == 1 ) {
      id = get_rotation();
    }
    else {
      bool rad = str2bool( elements[ 1 ] );
      id = get_rotation( rad );
    }
  }
  else if ( command == "move" && actionSize == 2  ) {
    int steps = str2int( elements[ 1 ] );
    motor_step( steps );
    success = true;
  }
  else if ( ( command == "set_pos" || command == "set_position" ) && actionSize == 2 ) {
    float pos = str2float( elements[ 1 ] );
    set_position( pos );
    success = true;
  }
  else if ( 
      ( command == "set_rot" || command == "set_rotation" ) 
      && ( actionSize == 2 || actionSize == 3 ) 
    ) {
    float rot = str2float( elements[ 1 ] );
    
    if ( actionSize == 2 ) {
       set_rotation( rot );
    }
    else {
      bool rad = str2bool( elements[ 2 ] );
      set_rotation( rot, rad );
    }
    
    success = true;
  }
  else if ( command == "offset" && actionSize == 2 ) {
    int num = str2int( elements[ 1 ] );
    update_motor_position( num );
    success = true;
  }
  else if ( command == "scan" ) {
    int homed[ STEPS_PER_ROTATION ];
    scan( homed );

    response = "[";
    for ( int i = 0; i < STEPS_PER_ROTATION; ++i ) {
      if ( homed[ i ] ) {
        response += String( i ) + ",";
      }
    }
    response.setCharAt( response.length() - 1, ']' );
    
    success = true;
  }
  else if ( command  == "home" ) {
    home();
    success = true;
  }
  else {
    // invalid command
    success = false;
  }

  String stat = "error";
  if ( success ) {
    stat = "success";
  }
  
  // send response
  const size_t respBufferSize = JSON_OBJECT_SIZE( 4 ) *2 + 100;
  StaticJsonDocument< respBufferSize > resp;

  resp[ "status" ]    = stat;
  resp[ "command" ]   = action;

  if ( id > -1 ) {
    resp[ "id" ] = id;
  }
  if ( response.length() > 0 ) {
    resp[ "response" ] = response;
  }
  
  serializeJson( resp, Serial );
  Serial.println();


  return id;
}
