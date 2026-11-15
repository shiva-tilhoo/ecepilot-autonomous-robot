TRAJECTORY EXPLAINED - THE PART AFTER WALL_CENTERING
Date: 2026-03-16

Context:
This note only describes the phase that starts AFTER the wall centering mode,
in simu_lidar_auto.py: the switch to a planned return with SIMPLE mode, A* and Nav2.


1) WHEN WALL_CENTERING ENDS

During auto_mode (wall centering), the system:
- records the points of the first lap (lap_points_m),
- detects that the robot is back near the start,
- keeps going for an extra distance (EXTRA_DISTANCE_AFTER_RETURN).

Once that distance is reached:
- auto_mode is switched off,
- SLAM is frozen through stop_slam_and_freeze_map() (/freeze_scan service),
- then the return strategy is started.


2) RETURN STRATEGY: SIMPLE MODE FIRST

The choice is driven by USE_SIMPLE_ASTAR_RETURN.

Nominal case (current): USE_SIMPLE_ASTAR_RETURN = True

Step A - "full loop" path (preferred)
- build_simple_full_loop_path_px() rebuilds a path from the lap already recorded.
- The path is:
  - resampled,
  - optimised with safe shortcuts (segment clearance),
  - slightly smoothed.

If this path exists (len > 1):
- simple_return_mode = True
- local path following with compute_simple_follow_command().

Step B - A* fallback (optional)
- If the full loop cannot be used:
  - if SIMPLE_REQUIRE_FULL_LOOP=True and SIMPLE_ALLOW_ASTAR_FALLBACK=False,
    the fallback is refused (logical safety),
  - otherwise plan_astar_path_px(start=current, goal=start point) computes a grid path.

If A* succeeds:
- simple_return_mode = True
- local PID following of the A* path.

If A* fails:
- switch to nav2_mode.


3) SIMPLE MODE: HOW THE ROBOT FOLLOWS THE PATH

Key function: compute_simple_follow_command(robot_pos, robot_theta, dt)

Principle:
- pick a target point ahead (lookahead),
- compute the heading error,
- PD angular command,
- linear speed modulated by the angular error,
- progressive braking near the end.

End criterion:
- last point reached within SIMPLE_GOAL_TOLERANCE_PX,
- simple_return_mode goes back to False.

Important:
- this mode does not use Nav2,
- it applies the motion directly in the simulation,
- it is deterministic and fast.


4) NAV2 MODE: WHEN AND HOW IT TAKES OVER

Nav2 is used if:
- USE_SIMPLE_ASTAR_RETURN=False,
- or SIMPLE mode is impossible / has failed.

Preparation:
- build_nav2_sequential_route_goals() generates a list of map-frame goals,
  oriented in the right direction of travel.

Execution:
- nav2_goal_pending drives the progressive sending,
- send_goal_to_start() sends each goal through NavigateToPose,
- on GOAL_SUCCEEDED: move on to the next goal,
- on GOAL_ABORTED/REJECTED/CANCELED: skip to the next one.

Specific point:
- publish_frozen_map_to_odom_transform() keeps map->odom "alive"
  even when SLAM is frozen, so that Nav2 does not break.


5) DIFFERENCE BETWEEN SIMPLE, A* AND NAV2

SIMPLE (recorded loop):
- path source: trajectory of the first lap,
- advantage: consistent with the corridor actually driven,
- limit: needs enough clean points.

A* fallback:
- path source: local grid planning in the track image,
- advantage: can save a return when there is no full loop,
- limit: depends on the quality of the grid and of the clearances.

Nav2:
- path source: Nav2 planner (DDS + action server),
- advantage: robust on the ROS2 navigation side,
- limit: more complex (actions, states, retries).


6) STATE MACHINE (AFTER WALL_CENTERING)

State 1: AUTO_MODE (wall centering)
  -> condition: return detected + extra distance reached
State 2: FREEZE_SLAM
  -> condition: is the SIMPLE strategy available?
State 3a: SIMPLE_RETURN_MODE
  -> if finished: END
  -> if impossible: NAV2_MODE
State 3b: NAV2_MODE
  -> sequential NavigateToPose goals sent
  -> goals finished: END


7) PARAMETERS DRIVING THIS PHASE

- USE_SIMPLE_ASTAR_RETURN
- SIMPLE_REQUIRE_FULL_LOOP
- SIMPLE_ALLOW_ASTAR_FALLBACK
- SIMPLE_GOAL_TOLERANCE_PX
- SIMPLE_LOOKAHEAD_PX
- SIMPLE_KP_HEADING / SIMPLE_KD_HEADING
- NAV2_ROUTE_GOAL_SPACING
- EXTRA_DISTANCE_AFTER_RETURN


8) SHORT SUMMARY

After wall_centering, the system freezes SLAM, then first tries a return in SIMPLE mode
(lap path), otherwise an A* fallback, and as a last resort switches to Nav2 with
sequential goals to complete the return to the start.
