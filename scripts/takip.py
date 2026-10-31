#!/usr/bin/env python3
"""Gazebo Harmonic için düz rota takip alıştırması; ROS gerektirmez.

İnsan konumu 02_insan.sdf içindeki önceden bilinen rotadan hesaplanır.
Görüntüden insan tespiti veya ölçülmüş insan pozisyonu değildir.
"""
import argparse
import math
import threading
import time

from gz.transport13 import Node
from gz.msgs10.odometry_pb2 import Odometry
from gz.msgs10.twist_pb2 import Twist


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--distance', type=float, choices=[0.6, 1.2, 2.0], default=1.2)
    args = parser.parse_args()
    node = Node()
    publisher = node.advertise('/model/hri_robot/cmd_vel', Twist)
    lock = threading.Lock()
    latest = {}

    def receive(msg):
        q = msg.pose.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y),
                         1 - 2 * (q.y * q.y + q.z * q.z))
        with lock:
            latest.update(t=msg.header.stamp.sec + msg.header.stamp.nsec / 1e9,
                          x=msg.pose.position.x, y=msg.pose.position.y,
                          yaw=yaw, received=time.monotonic())

    node.subscribe(Odometry, '/model/hri_robot/odometry', receive)
    print(f'Takip hedefi {args.distance} m. Simülasyonda Play düğmesine basın.', flush=True)
    print('İnsan konumu bilinen rotadan tahmin ediliyor; bu bir öğrenme demosudur.', flush=True)
    last_print = -1
    started = time.monotonic()
    try:
        while True:
            with lock:
                state = dict(latest)
            command = Twist()
            if state and time.monotonic() - state['received'] < 0.5:
                t = state['t']
                if t >= 33:
                    print('Yürüme rotası tamamlandı; robot durduruluyor.', flush=True)
                    break
                # SDF rota noktaları: ilk 3 s x=3; sonra 1 m/s ile +X.
                person_x = 3 + max(0, t - 3)
                # Model ön kenarı 0.342 m, varsayılan sırt ofseti 0.15 m.
                # Meshin yürüyüş salınımını ve gerçek sırt yüzeyini ölçmez.
                desired_x = person_x - args.distance - 0.342 - 0.15
                dx, dy = desired_x - state['x'], -state['y']
                heading = math.atan2(dy, max(0.05, dx)) - state['yaw']
                heading = math.atan2(math.sin(heading), math.cos(heading))
                feedforward = 1.0 if t >= 3 else 0.0
                command.linear.x = max(0.0, min(2.0, feedforward + 0.8 * dx))
                command.linear.x *= max(0.0, math.cos(heading))
                command.angular.z = max(-1.0, min(1.0, 2 * heading))
                if int(t) != last_print:
                    gap = person_x - state['x'] - 0.492
                    print(f't={t:4.1f} s | tahmini boşluk={gap:.2f} m | hız komutu={command.linear.x:.2f} m/s', flush=True)
                    last_print = int(t)
            elif not state and time.monotonic() - started > 60:
                raise RuntimeError('60 saniyedir konum verisi yok. Doğru sahne ve Play durumunu kontrol edin.')
            publisher.publish(command)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print('\nTakip durduruldu.', flush=True)
    finally:
        for _ in range(5):
            publisher.publish(Twist())
            time.sleep(0.05)


if __name__ == '__main__':
    main()
