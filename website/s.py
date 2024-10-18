def calculate_fare(fare_AB, fare_BC, fare_CD, passengers_A_in, passengers_B_in, passengers_B_out, passengers_C_in, passengers_D_out):
    total_passengers_A = passengers_A_in
    total_passengers_B = passengers_B_in + (total_passengers_A - passengers_B_out)
    total_passengers_C = passengers_C_in + total_passengers_B

    total_fare_owed_entering = -passengers_B_in * fare_AB - passengers_C_in * (fare_AB + fare_BC)
    total_fare_paid_exiting = passengers_B_out * fare_AB + passengers_D_out * (fare_AB + fare_BC + fare_CD)

    net_total_fare = total_fare_owed_entering + total_fare_paid_exiting
    return net_total_fare

fare_AB = 30
fare_BC = 30
fare_CD = 40
passengers_A_in = 5
passengers_B_in = 10
passengers_B_out = 3
passengers_C_in = 6
passengers_D_out = 18

result = calculate_fare(fare_AB, fare_BC, fare_CD, passengers_A_in, passengers_B_in, passengers_B_out, passengers_C_in, passengers_D_out)

print(f"Net Fare: {result} Ksh")