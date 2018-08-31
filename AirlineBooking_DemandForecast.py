
import os
import numpy as np
import pandas as pd

os.chdir("M:/2018_Winter_Quarter/Programming for Business Analytics/Python/GroupProject") 

# Function to calculate Days Prior and Day Of Week
def calculateDPDD(x):
        # Calculate days prior
        x["Days_Prior"]    = (pd.to_datetime(x['departure_date']).sub(pd.to_datetime(x['booking_date']))).dt.days        
        # Calculate day of the week
        x["Departure_day"] = (pd.to_datetime(x['departure_date']).sub(pd.to_datetime(x['booking_date']))).dt.days
        x["Departure_day"] = pd.to_datetime(x['departure_date']).dt.weekday_name

# Function to calculate demand based on Forecasting Method
def calculateDemand(Training_Data,forecast_method):  
    #For Additive Model
    if forecast_method == 1:
        Training_Data['demand'] = Training_Data['cum_bookings_y'] - Training_Data['cum_bookings_x']
    #For Mutiplicative Model
    elif forecast_method == 2:
        Training_Data['demand'] = Training_Data['cum_bookings_x'] / Training_Data['cum_bookings_y']
    #For Mutiplicative Model by Daily Growth
    else:
        Training_Data = Training_Data.sort_values(by=['departure_date', 'Days_Prior'], ascending=[True,True])  
        Training_Data['sft_cum_book'] = Training_Data.groupby('departure_date')['cum_bookings_x'].shift(-1)      
        Training_Data['demand'] = Training_Data['cum_bookings_x']/Training_Data['sft_cum_book']  
        # Remove unwanted records
        Training_Data = Training_Data.drop(Training_Data[Training_Data["demand"].isnull() == True].index)
        Training_Data = Training_Data.drop(Training_Data[Training_Data["demand"] == np.inf].index)

    return Training_Data

# Function to calculate forecast based on Forecasting Method
def calculateForecast(Training_Data,Validation_Data, forecast_method):   
    
    T_Data = Training_Data.merge(Validation_Data, left_on =['Days_Prior','Departure_day'], right_on = ['Days_Prior','Departure_day'])
    T_Data['Neighbor_Distance'] = abs(T_Data['cum_bookings'] - T_Data['cum_bookings_x'])
    
    #Sort the data frame
    T_Data = T_Data.sort_values(by=["Days_Prior", "Departure_day", "Neighbor_Distance"], ascending=[True,True,True])
    
    #Subset the records to fetch only the 4 nearest neighbours 
    T_Data = T_Data.groupby(['Days_Prior','Departure_day']).head(4).reset_index(drop=True)
    
    #Take the average of calculated demand based on Days Prior and Day Of Week
    T_Data = T_Data.groupby(['Days_Prior','Departure_day'], as_index=False)["demand"].mean()
    
    #Join Training and validation dataset to calculate the Forecast
    Validation_Data = Validation_Data.merge(T_Data, left_on =['Days_Prior','Departure_day'], right_on = ['Days_Prior','Departure_day'])
        
    if forecast_method == 1:
        Validation_Data['Forecast'] = Validation_Data['cum_bookings'] + Validation_Data['demand']
    elif forecast_method == 2 or forecast_method == 3:
        Validation_Data['Forecast'] = Validation_Data['cum_bookings'] / Validation_Data['demand']
        
    V_Data = Validation_Data[['departure_date','booking_date','final_demand','Forecast','naive_forecast']]
    
    return V_Data
    
def calculateMase(V_Data): 
    #Calculate Mean Forecast Error
    Mean_Forecast_Error     = ((V_Data['final_demand'] - V_Data['Forecast']).sum()) / len(V_Data)
    #Calculate Mean Absolute Deviation
    Mean_Absolute_Deviation = (((V_Data['final_demand'] - V_Data['Forecast']).abs()).sum()) / len(V_Data)
    #Calculate Standard Deviation
    Standard_Deviation      = np.sqrt(((V_Data['final_demand'] - V_Data['Forecast'])**2).sum() / len(V_Data))
    #Calculate MASE
    MASE = (((V_Data['final_demand'] - V_Data['Forecast']).abs()).sum()) / (((V_Data['final_demand'] - V_Data['naive_forecast']).abs()).sum())
    
    
    output = "\n" + "Mean Forecast Error: " + str(Mean_Forecast_Error) + "\n" + "Mean Absolute Deviation: " + str(Mean_Absolute_Deviation) + "\n"+  "Standard Deviation: " + str(Standard_Deviation) + "\n"+ "MASE:" + str(MASE)
      
    return V_Data, output
    
def airlineForecast(inp_train_file, inp_valid_file, forecast_method):
    
    #Read the records from Training Data File
    Training_Data   = pd.read_csv(inp_train_file, sep=',', header=0)
    #Read the records from Validation Data File 
    Validation_Data = pd.read_csv(inp_valid_file, sep=',', header=0)
    
    #Call function to calculate Days Prior and Day Of Week in Training Data set 
    calculateDPDD(Training_Data)
    
    #remove the records for which days prior is greater than 28
    Training_Data = Training_Data.drop(Training_Data[Training_Data['Days_Prior'] > 28].index)
    
    #Subset the records where 'Days Prior' = 0
    Temp = Training_Data.loc[Training_Data['Days_Prior']==0, ['departure_date','cum_bookings']]
    
    #Joined multiple columns based on Departure Date 
    Training_Data = Training_Data.merge(Temp, left_on =['departure_date'], right_on = ['departure_date'])
    
    #Call function to calculate Days Prior and Day Of Week in Validation Data set
    calculateDPDD(Validation_Data)
    Validation_Data = Validation_Data.drop(Validation_Data[Validation_Data['Days_Prior']==0].index)
    
    #Call function to calculate Demand
    Training_Data = calculateDemand(Training_Data,forecast_method) 
    
    #Call function to calculate Forecast
    V_Data = calculateForecast(Training_Data, Validation_Data, forecast_method)
    
    #Call function to calculate Mean Forecast Error, Mean Absolute Deviation, Standard Deviation & MASE
    MASE = calculateMase(V_Data)
    
    return MASE

def main():
    
    #Display the list of Forecasting Method
    print("\n" + "Airline Forecast Models:" + "\n" + "1: Additive" + "\n" + "2: Multiplicative" + "\n" + "3: Multiplicative(Daily Growth)")
    
    #Take input from user to select any of the Forecasting Method
    while True:
        Forecast_Method = raw_input("Select one of the aforementioned Forecasting Model(number only from 1 to 3) : ")
        if str(Forecast_Method).isalpha():
            print("Invalid Value! Please enter number only")
            continue
        elif int(Forecast_Method) not in [1,2,3]:
            print("Please enter the choice between 1 & 3")
            continue
        else:
            Forecast_Method = int(Forecast_Method)
            break
    
    MASE = airlineForecast("airline_booking_trainingData.csv", "airline_booking_validationData_revised.csv", Forecast_Method)
    print MASE
    
main()             

# End of Code
######################################################################################################################################## 