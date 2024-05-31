from math import sqrt, cos, sin , pi
from enum import Enum
import folium

class H_Action(Enum):
    """
    Horizontal action that can be perform by the aircraft
    """

    up = -1
    straight = 0
    down = 1


class V_Action(Enum):
    """
    Vertical action that can be perform by the aircraft
    """

    climb = 1
    cruise = 0
    descent = -1

def plot_map(path, G, domain):
    m = folium.Map(
        location=[
            0.5 * (domain.lat1 + domain.lat2),
            0.5 * (domain.lon1 + domain.lon2)
        ],
        zoom_start=5)
    
    for f in G.nodes:
        folium.Marker(
            location=[
                domain.network[f[0]][f[1]][f[2]].lat,
                domain.network[f[0]][f[1]][f[2]].lon
            ],
            popup=str(f),
            icon=folium.Icon(color="beige"),
        ).add_to(m)

    for (f,t) in G.edges:
        folium.PolyLine(
            locations=[
                (domain.network[f[0]][f[1]][f[2]].lat, domain.network[f[0]][f[1]][f[2]].lon),
                (domain.network[t[0]][t[1]][t[2]].lat, domain.network[t[0]][t[1]][t[2]].lon)
            ],
            color='beige'
        ).add_to(m)

    folium.Marker(
        location=[
            domain.lat1,
            domain.lon1
        ],
        popup="origin",
        icon=folium.Icon(color="blue"),
    ).add_to(m)
    folium.Marker(
        location=[
            domain.lat2,
            domain.lon2
        ],
        popup="arrival",
        icon=folium.Icon(color="red"),
    ).add_to(m)

    for i in range(len(path)-1):
        p=path[i]
        pp=path[i+1]
        folium.Marker(
            location=[
                domain.network[p[0]][p[1]][p[2]].lat,
                domain.network[p[0]][p[1]][p[2]].lon
            ],
            popup=str(p),
            icon=folium.Icon(color="green"),
        ).add_to(m)
        folium.PolyLine(
            locations=[
                ( domain.network[p[0]][p[1]][p[2]].lat, domain.network[p[0]][p[1]][p[2]].lon),
                (domain.network[pp[0]][pp[1]][pp[2]].lat, domain.network[pp[0]][pp[1]][pp[2]].lon)
            ],
            color='green'
        ).add_to(m)
    return m

def cost(domain,f,t):
    EARTH_RADIUS = 3440 
    wp1 = domain.network[f[0]][f[1]][f[2]]
    wp2 = domain.network[t[0]][t[1]][t[2]]

    AIRCRAFT_SPEED = 500
    WIND_DIRECTION = domain.weather_interpolator.interpol_wind_classic(wp1.lat,wp1.lon,0,34*wp1.height)[1] * 180
    WIND_SPEED = domain.weather_interpolator.interpol_wind_classic(wp1.lat,wp1.lon,0,34*wp1.height)[0]
    # Computes coordinates of the direction vector in the Earth-centered system
    dir_x = EARTH_RADIUS * (
        (cos(wp2.lat * pi / 180.0) * cos(wp2.lon * pi / 180.0))
        - (cos(wp1.lat * pi / 180.0) * cos(wp1.lon * pi / 180.0))
    )
    dir_y = EARTH_RADIUS * (
        (cos(wp2.lat * pi / 180.0) * sin(wp2.lon * pi / 180.0))
        - (cos(wp1.lat * pi / 180.0) * sin(wp1.lon * pi / 180.0))
    )
    dir_z = EARTH_RADIUS * (
        sin(wp2.lat * pi / 180.0) - sin(wp1.lat * pi / 180.0)
    )
    # Computes coordinates of the direction vector in the tangential plane at the waypoint node.data
    dir_a = (-dir_x * sin(wp1.lon * pi / 180.0)) + (
        dir_y * cos(wp1.lon * pi / 180.0)
    )
    dir_b = (
        (
            dir_x
            * (
                -sin(wp1.lat * pi / 180.0)
                * cos(wp1.lon * pi / 180.0)
            )
        )
        + (
            dir_y
            * (
                -sin(wp1.lat * pi / 180.0)
                * sin(wp1.lon * pi / 180.0)
            )
        )
        + (dir_z * cos(wp1.lat * pi / 180.0))
    )
    # Normalize the direction vector
    dir_na = dir_a / sqrt(dir_a * dir_a + dir_b * dir_b)
    dir_nb = dir_b / sqrt(dir_a * dir_a + dir_b * dir_b)
    # Compute wind vector in the tangential plane
    w_a = WIND_SPEED * sin(WIND_DIRECTION * pi / 180.0)
    w_b = WIND_SPEED * cos(WIND_DIRECTION * pi / 180.0)
    # Compute speed along direction vector
    mu = (dir_na * w_a) + (dir_nb * w_b)
    phi = (
        (mu * mu)
        - (WIND_SPEED * WIND_SPEED)
        + (AIRCRAFT_SPEED * AIRCRAFT_SPEED)
    )
    dir_speed = mu + sqrt(phi)
    flown_distance = (
        AIRCRAFT_SPEED * sqrt(dir_a * dir_a + dir_b * dir_b) / dir_speed
    )
    return flown_distance