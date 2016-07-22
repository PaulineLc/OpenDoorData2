from myapp import app
import pymysql
import pandas as pd

def main():
    
    #Connect to database
    configdb = app.config['DATABASE']
    
    conn = pymysql.connect(db = 'wifi_db',
                           host = configdb['host'],
                          user = configdb['user'],
                          password =configdb['password']
                          )
    
    wifi_logs = pd.read_sql('select * from wifi_log;', con=conn)

    room_data = pd.read_sql('select * from room;', con=conn)
    predict_coef = 0.884521 #at a later stage,this will be imported from the db
    
    #Create datetime object column, and set it as index
    #This is required to merge the data based on date and time
    wifi_logs['event_time'] = pd.to_datetime(wifi_logs.event_time, unit='s')
    wifi_logs.set_index('event_time', inplace=True)
    
    # create new columns, event_hour, event_day, event_month and event_year. This is to merge on it.
    wifi_logs['event_year'] = wifi_logs.index.year
    wifi_logs['event_month'] = wifi_logs.index.month
    wifi_logs['event_day'] = wifi_logs.index.day
    wifi_logs['event_hour'] = wifi_logs.index.hour

    wifi_logs = wifi_logs.groupby(['building','room_id', 'event_day', 'event_hour', 'event_month', 'event_year'], 
                                  as_index=False).median()

    #Calculate predicted occupancy
    wifi_logs['occupancy_pred'] = None
    for i in range(wifi_logs.shape[0]):
        wifi_logs.set_value(i, 'occupancy_pred', 
                            wifi_logs['auth_devices'][i] * predict_coef)
    
    #add categories
    wifi_logs['occupancy_category_5'] = None
    wifi_logs['occupancty_category_3'] = None
    wifi_logs['binary_occupancy'] = None

    for i in range(wifi_logs.shape[0]):
        room = wifi_logs['room_id'][i]
        building = wifi_logs['building'][i]

        capacity = room_data['room_cap'].loc[(room_data['room_num'] == room) & (room_data['building'] == building)].values[0]
        
        prediction = set_occupancy_category(wifi_logs['occupancy_pred'][i], capacity)
        
        wifi_logs.set_value(i, 'occupancy_category_5', prediction[0])
        wifi_logs.set_value(i, 'occupancty_category_3', prediction[1])
        wifi_logs.set_value(i, 'binary_occupancy', prediction[2])
    
    json_file = wifi_logs[['building', 
                           'room_id', 
                           'event_day', 
                           'event_hour', 
                           'event_month', 
                           'event_year', 
                           'occupancy_category_5', 
                           'occupancty_category_3',
                           'binary_occupancy']].to_json()
    
    print(json_file)
    
def set_occupancy_category(occupants, capacity):
    '''function that converts linear predictions to a defined category.
    
    Parameters
    ----------
    occupants: the number of occupants (real or predicted)
    capacity: the room capacity
    
    Returns
    ---------
    tuple with 3 values: 
        at position 0, the occupancy with 5 cateories
        at position 1, the occupancy with 3 categories
        at position 2, the binary occupancy
    
    '''
    
    ratio = occupants/capacity
    
    # assign category based on ratio
    if ratio < 0.125:
        cat5 = 0.0
    elif ratio < 0.375:
        cat5 =  0.25
    elif ratio < 0.625:
        cat5 =  0.5
    elif ratio < 0.875:
        cat5 =  0.75
    else:
        cat5 =  1.0
    
    cat3 = "empty" if cat5 < 0.25 else "moderate" if cat5 < 0.75 else "full" if cat5>= 0.75 else "ERROR"
    
    cat2 = False if cat3 == "empty" else True
    
    return cat5, cat3, cat2 #This will return a tuple

    
if __name__ == "__main__":
    main()