#!/usr/bin/env python3

# Author: Mani Amoozadeh
# Email: mani.amoozadeh2@gmail.com

import os
import logging
from flask import Flask, Blueprint, render_template, request
from flask import send_from_directory, jsonify
from flask_restx import Api, Resource
from qmp_client import QMPClient

#################################

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

#################################

app = Flask(__name__)

log.info("Starting QMPClient...")
qmp_client = QMPClient('./qmp-sock')
response = qmp_client.execute('query-version')
log.info("QEMU version:\n     %s", response)
log.info("")

#################################

# Create a blueprint for the web routes
web_bp = Blueprint("web", __name__, template_folder="templates")

@web_bp.route("/")
def home():
    return render_template("index.html")

# legacy browsers
@web_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Register blueprint for web routes
app.register_blueprint(web_bp)

#################################

# Initialize Flask-RESTX API
api = Api(app,
          version="1.0",
          title="QEMU QMP API",
          description="QEMU VM Introspection and Control",
          prefix="/api",
          doc="/api/docs")

# Define API Namespace
ns = api.namespace("v1", description="QMP Commands")

#################################

# Test with: curl http://localhost:5000/api/v1/commands

@ns.route("/commands")
class VMCommands(Resource):
    def get(self):
        return qmp_client.execute("query-commands")

######## General VM Info ########

@ns.route("/status")
class VMStatus(Resource):
    def get(self):
        # Get the current VM run state (e.g. running, paused).
        return qmp_client.execute("query-status")

@ns.route("/version")
class QemuVersion(Resource):
    def get(self):
        # Retrieve QEMU build and version information.
        return qmp_client.execute("query-version")

@ns.route("/machine")
class MachineTypes(Resource):
    def get(self):
        # List supported machine types for the current target.
        return qmp_client.execute("query-machines")

@ns.route("/target")
class TargetArch(Resource):
    def get(self):
        # Show the QEMU architecture target (e.g. x86_64, aarch64).
        return qmp_client.execute("query-target")

@ns.route("/name")
class VMName(Resource):
    def get(self):
        # Get the name assigned to the VM (via -name).
        return qmp_client.execute("query-name")

@ns.route("/uuid")
class VMUUID(Resource):
    def get(self):
        # Get the VM’s UUID (universally unique identifier).
        return qmp_client.execute("query-uuid")

######## CPU & Memory ########

@ns.route("/cpus")
class VMCpus(Resource):
    def get(self):
        # Get info on all virtual CPUs (e.g. state, thread ID).
        return qmp_client.execute("query-cpus-fast")

@ns.route("/cpu-defs")
class CPUDefinitions(Resource):
    def get(self):
        # List CPU model definitions supported by the accelerator.
        return qmp_client.execute("query-cpu-definitions")

@ns.route("/memory")
class MemorySummary(Resource):
    def get(self):
        # Get total and used memory reported by QEMU.
        return qmp_client.execute("query-memory-size-summary")

@ns.route("/memdevs")
class MemoryDevices(Resource):
    def get(self):
        # List memory backend objects configured in the VM.
        return qmp_client.execute("query-memory-devices")

######## Block Devices ########

@ns.route("/block")
class VMBlock(Resource):
    def get(self):
        # Show runtime status of attached block devices (disks).
        return qmp_client.execute("query-block")

@ns.route("/block/named")
class VMBlockNodes(Resource):
    def get(self):
        # List internal node names for block devices (used in snapshots, migration, etc.).
        return qmp_client.execute("query-named-block-nodes")

######## PCI / Devices ########

@ns.route("/devices")
class VMDevices(Resource):
    def get(self):
        # List PCI devices visible to the guest.
        return qmp_client.execute("query-pci")

@ns.route("/pci")
class VMPCIInfo(Resource):
    def get(self):
        # Same as /devices, shows PCI topology.
        try:
            return qmp_client.execute("query-pci")
        except Exception as e:
            return {"error": str(e)}, 500

######## Char, Display, I/O ########

@ns.route("/chardev")
class VMChardev(Resource):
    def get(self):
        # Get a list of currently defined character devices.
        return qmp_client.execute("query-chardev")

@ns.route("/chardev-backends")
class ChardevBackends(Resource):
    def get(self):
        # 	List supported chardev backend types (e.g. file, socket).
        return qmp_client.execute("query-chardev-backends")

@ns.route("/display")
class VMDisplay(Resource):
    def get(self):
        # Show current display settings (e.g. VNC, curses).
        return qmp_client.execute("query-display-options")

@ns.route("/iothreads")
class VMIoThreads(Resource):
    def get(self):
        # List I/O threads running in the VM.
        return qmp_client.execute("query-iothreads")

######## Stats & Balloon ########

@ns.route("/stats")
class VMStats(Resource):  # FIXME
    def get(self):
        # Query enabled VM statistics (e.g. block, net, memory).
        return qmp_client.execute("query-stats")

@ns.route("/balloon")
class VMBalloon(Resource):
    def get(self):
        # Show current memory ballooning status (if enabled).
        return qmp_client.execute("query-balloon")

######## QOM (QEMU Object Model) ########

@ns.route("/qom-tree")
class QOMTree(Resource):
    def get(self):
        # List the QOM hierarchy from the root path /.
        return qmp_client.execute("qom-list", {"path": "/"})

@ns.route("/qom-types")
class QOMTypes(Resource):
    def get(self):
        # List all available QOM object types.
        return qmp_client.execute("qom-list-types")

@ns.route("/qom-props/<path:path>")
class QOMProperties(Resource):
    def get(self, path):
        # Show all QOM properties for a specific object path.
        return qmp_client.execute("qom-list-properties", {"path": f"/{path}"})

######## Debug / Developer Tools ########

@ns.route("/qmp-schema")
class QMPCommandSchema(Resource):
    def get(self):
        # Get the full QMP command schema (name, args, doc).
        return qmp_client.execute("query-qmp-schema")

@ns.route("/interrupts")
class VMInterrupts(Resource):
    def get(self):
        # Query IRQ (interrupt request) configuration.
        return qmp_client.execute("x-query-irq")

@ns.route("/roms")
class QemuRoms(Resource):
    def get(self):
        # List firmware/ROMs loaded by QEMU.
        return qmp_client.execute("x-query-roms")

@ns.route("/trace-events/<string:name>")
class TraceEvent(Resource):
    def get(self, name):
        # Get the state of a specific trace event by name.
        return qmp_client.execute("trace-event-get-state", {"name": name})

######## Snapshot ########

@ns.route("/snapshot/devices")
class SnapshotDevices(Resource):
    def get(self):
        # Return list of snapshot-eligible device node names (qcow2 + writable).
        nodes = qmp_client.execute("query-named-block-nodes")["return"]
        return [
            node["node-name"]
            for node in nodes
            if node.get("drv") == "qcow2" and not node.get("ro") and node.get("node-name")
        ]


# curl "http://localhost:5000/api/v1/snapshot/save?tag=snap1&job-id=save_snap1&vmstate=%23block131&devices=%23block131"
@ns.route("/snapshot/save")
class SaveSnapshot(Resource):
    def get(self):
        try:
            tag = request.args.get("tag")
            job_id = request.args.get("job-id")
            vmstate = request.args.get("vmstate")
            devices_str = request.args.get("devices")

            # Validate required fields
            if not all([tag, job_id, vmstate, devices_str]):
                return {
                    "error": "Missing one or more required query parameters: tag, job-id, vmstate, devices"
                }, 400

            devices = [d.strip() for d in devices_str.split(",") if d.strip()]
            if not devices:
                return {"error": "devices list cannot be empty"}, 400

            return qmp_client.execute("snapshot-save", {
                "tag": tag,
                "job-id": job_id,
                "vmstate": vmstate,
                "devices": devices
            })

        except Exception as e:
            return {"error": str(e)}, 500


@ns.route("/snapshot/load")
class LoadSnapshot(Resource):
    def get(self):
        try:
            tag = request.args.get("tag")
            job_id = request.args.get("job-id")
            vmstate = request.args.get("vmstate")
            devices_str = request.args.get("devices")

            # Validate required fields
            if not all([tag, job_id, vmstate, devices_str]):
                return {
                    "error": "Missing one or more required query parameters: tag, job-id, vmstate, devices"
                }, 400

            devices = [d.strip() for d in devices_str.split(",") if d.strip()]
            if not devices:
                return {"error": "devices list cannot be empty"}, 400

            return qmp_client.execute("snapshot-load", {
                "tag": tag,
                "job-id": job_id,
                "vmstate": vmstate,
                "devices": devices
            })

        except Exception as e:
            return {"error": str(e)}, 500


@ns.route("/snapshot/delete")
class DeleteSnapshot(Resource):
    def get(self):
        try:
            tag = request.args.get("tag")
            job_id = request.args.get("job-id")
            devices_str = request.args.get("devices")

            if not all([tag, job_id, devices_str]):
                return {"error": "Missing one or more required query parameters: tag, job-id, devices"}, 400

            devices = [d.strip() for d in devices_str.split(",") if d.strip()]
            if not devices:
                return {"error": "devices list cannot be empty"}, 400

            return qmp_client.execute("snapshot-delete", {
                "tag": tag,
                "job-id": job_id,
                "devices": devices
            })
        except Exception as e:
            return {"error": str(e)}, 500


@ns.route("/snapshot/status/<string:job_id>")
class SnapshotStatus(Resource):
    def get(self, job_id):
        try:
            jobs = qmp_client.execute("query-jobs")
            for job in jobs["return"]:
                if job.get("id") == job_id:
                    return job
            return {"error": f"Job ID '{job_id}' not found"}, 404
        except Exception as e:
            return {"error": str(e)}, 500


@ns.route("/snapshot/list")
class SnapshotStatus(Resource):
    def get(self):
        try:
            result = qmp_client.execute("human-monitor-command", {
                "command-line": "info snapshots"
            })
            raw_output = result["return"]
            return jsonify({"snapshots": raw_output})
        except Exception as e:
            return {"error": str(e)}, 500

#####################################

@ns.route("/uptime")
class VMUptime(Resource):
    def get(self):
        return qmp_client.execute("query-uptime")

@ns.route("/guest/processes")
class GuestProcesses(Resource):
    def get(self):
        return qmp_client.execute("guest-get-processes")

#####################################

@ns.route("/vm/start")
class StartVM(Resource):
    def get(self):
        return qmp_client.execute("cont")

@ns.route("/vm/stop")
class StopVM(Resource):
    def get(self):
        return qmp_client.execute("stop")

@ns.route("/vm/reset")
class ResetVM(Resource):
    def get(self):
        return qmp_client.execute("system_reset")


if __name__ == '__main__':

    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
