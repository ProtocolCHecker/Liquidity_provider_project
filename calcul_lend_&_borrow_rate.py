#formula to calculate borrowing rate

def borrowing_and_lending_rate(slope1, slope2, U_optimal, reserve_factor, base_rate, utilization_rate):
    
    if utilization_rate <= U_optimal:
        borrow_rate = base_rate + slope1 * utilization_rate
    else:
        br = base_rate + slope1 * utilization_rate + ((utilization_rate - U_optimal)/(1 - U_optimal))
    lending_rate = borrow_rate * (1 - reserve_factor)

    return borrow_rate, lending_rate