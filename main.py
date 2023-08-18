import os
import asyncio
from flask import Flask, request, jsonify
from threading import Timer
from smartrent import async_login

class HomeControl:
    SECRET = os.environ.get('SECRET')
    TEMP_UPDATE_INTERVAL = 300
    VALID_PATHS = ['kitchen', 'bedroom', 'door', 'toggle_thermostat', 'current_temp', 'increase_temp', 'decrease_temp']

    def __init__(self):
        self.app = Flask(__name__)
        self.current_temp = 0
        self.tmp_temp = 0
        self.show_tmp_temp = False

        self.app.add_url_rule('/', view_func=self.log_route, methods=['POST'])
        self.app.add_url_rule('/<path:room>', view_func=self.control_room, methods=['POST'])

    async def log_route(self):
        print(request.path)
        return ('', 204)

    async def control_room(self, room):
        if room not in self.VALID_PATHS or request.json.get('secret') != self.SECRET:
            return jsonify(status="invalid")

        if room == 'kitchen':
            await self.toggle_device(self.kitchen)
            return jsonify(status=self.kitchen.get_on())

        if room == 'bedroom':
            await self.toggle_device(self.bedroom)
            return jsonify(status=self.bedroom.get_on())

        if room == 'door':
            await self.toggle_lock(self.door)
            return jsonify(status=self.door.get_locked())

        if room == 'toggle_thermostat':
            return await self.toggle_thermostat(self.thermostat)

        if room == 'current_temp':
            display_temp = f"*{self.tmp_temp}*" if self.show_tmp_temp else self.current_temp
            self.show_tmp_temp = False
            return jsonify(value=display_temp)

        if room in ['decrease_temp', 'increase_temp']:
            return await self.adjust_temp(self.thermostat, room)

    async def toggle_device(self, device):
        await device.async_set_on(not device.get_on())

    async def toggle_lock(self, lock_device):
        await lock_device.async_set_locked(not lock_device.get_locked())

    async def toggle_thermostat(self, thermo_device):
        current_mode = thermo_device.get_mode()
        new_mode = 'off' if current_mode == 'cool' else 'cool'
        await thermo_device.async_set_mode(new_mode)
        return jsonify(status='Off' if new_mode == 'off' else 'On')

    async def adjust_temp(self, thermo_device, action):
        current_setpoint = thermo_device.get_cooling_setpoint()
        adjustment = 1 if action == 'increase_temp' else -1
        new_setpoint = current_setpoint + adjustment
        await thermo_device.async_set_cooling_setpoint(new_setpoint)
        self.tmp_temp = new_setpoint
        self.show_tmp_temp = True

        return ('', 200)

    def update_temp(self):
        self.current_temp = self.thermostat.get_current_temp()

    async def main(self):
        self.api = await async_login(os.environ.get('EMAIL'), os.environ.get('PASSWORD'))
        self.thermostat = self.api.get_thermostats()[0]
        self.kitchen = self.api.get_binary_switches()[0]
        self.bedroom = self.api.get_binary_switches()[1]
        self.door = self.api.get_locks()[0]

        self.update_temp()
        Timer(self.TEMP_UPDATE_INTERVAL, self.update_temp).start()

        self.app.run(host='0.0.0.0', port=os.environ.get('PORT'))

if __name__ == '__main__':
    controller = HomeControl()
    asyncio.run(controller.main())