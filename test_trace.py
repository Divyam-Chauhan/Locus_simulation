import math

def calculate_bearing(x_click, y_click):
    # Constants
    speed_of_sound = 343.0 # m/s
    pixels_per_meter = 800.0
    center_x, center_y = 300.0, 300.0
    mic_dist_pixels = 0.075 * pixels_per_meter # 60 pixels
    
    # Mic coordinates
    mics = {
        'N': (center_x, center_y - mic_dist_pixels),
        'E': (center_x + mic_dist_pixels, center_y),
        'S': (center_x, center_y + mic_dist_pixels),
        'W': (center_x - mic_dist_pixels, center_y)
    }
    
    # Calculate absolute time of flight (us)
    times_us = {}
    for name, (mx, my) in mics.items():
        dist_px = math.sqrt((x_click - mx)**2 + (y_click - my)**2)
        dist_m = dist_px / pixels_per_meter
        time_s = dist_m / speed_of_sound
        times_us[name] = time_s * 1_000_000.0
        
    # Relative timestamps
    min_time = min(times_us.values())
    rel_times_us = {name: t - min_time for name, t in times_us.items()}
    
    # TDOA Math Engine
    dt_x = times_us['E'] - times_us['W']
    dt_y = times_us['N'] - times_us['S']
    
    angle_rad = math.atan2(-dt_y, -dt_x)
    bearing = 90.0 - math.degrees(angle_rad)
    bearing = bearing % 360.0
    
    return dt_x, dt_y, bearing, rel_times_us

def run_tests():
    print("--- LOCUS TEST TRACE ---")
    
    # North
    print("Test 1: Click exactly North (300, 100)")
    dx, dy, b, t = calculate_bearing(300, 100)
    print(f"  dx: {dx:.2f}, dy: {dy:.2f}")
    print(f"  Bearing: {b:.2f}° (Expected: 0.00°)")
    assert math.isclose(b, 0.0, abs_tol=0.1) or math.isclose(b, 360.0, abs_tol=0.1)
    
    # North-East
    print("\nTest 2: Click exactly North-East (400, 200)")
    dx, dy, b, t = calculate_bearing(400, 200)
    print(f"  dx: {dx:.2f}, dy: {dy:.2f}")
    print(f"  Bearing: {b:.2f}° (Expected: 45.00°)")
    assert math.isclose(b, 45.0, abs_tol=0.1)

    # East
    print("\nTest 3: Click exactly East (500, 300)")
    dx, dy, b, t = calculate_bearing(500, 300)
    print(f"  dx: {dx:.2f}, dy: {dy:.2f}")
    print(f"  Bearing: {b:.2f}° (Expected: 90.00°)")
    assert math.isclose(b, 90.0, abs_tol=0.1)
    
    # South-East
    print("\nTest 4: Click exactly South-East (400, 400)")
    dx, dy, b, t = calculate_bearing(400, 400)
    print(f"  dx: {dx:.2f}, dy: {dy:.2f}")
    print(f"  Bearing: {b:.2f}° (Expected: 135.00°)")
    assert math.isclose(b, 135.0, abs_tol=0.1)
    
    # South
    print("\nTest 5: Click exactly South (300, 500)")
    dx, dy, b, t = calculate_bearing(300, 500)
    print(f"  dx: {dx:.2f}, dy: {dy:.2f}")
    print(f"  Bearing: {b:.2f}° (Expected: 180.00°)")
    assert math.isclose(b, 180.0, abs_tol=0.1)

    # South-West
    print("\nTest 6: Click exactly South-West (200, 400)")
    dx, dy, b, t = calculate_bearing(200, 400)
    print(f"  dx: {dx:.2f}, dy: {dy:.2f}")
    print(f"  Bearing: {b:.2f}° (Expected: 225.00°)")
    assert math.isclose(b, 225.0, abs_tol=0.1)

    # West
    print("\nTest 7: Click exactly West (100, 300)")
    dx, dy, b, t = calculate_bearing(100, 300)
    print(f"  dx: {dx:.2f}, dy: {dy:.2f}")
    print(f"  Bearing: {b:.2f}° (Expected: 270.00°)")
    assert math.isclose(b, 270.0, abs_tol=0.1)

    # North-West
    print("\nTest 8: Click exactly North-West (200, 200)")
    dx, dy, b, t = calculate_bearing(200, 200)
    print(f"  dx: {dx:.2f}, dy: {dy:.2f}")
    print(f"  Bearing: {b:.2f}° (Expected: 315.00°)")
    assert math.isclose(b, 315.0, abs_tol=0.1)
    
    print("\nAll tests passed successfully!")

if __name__ == '__main__':
    run_tests()
