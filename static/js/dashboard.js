
document.addEventListener("DOMContentLoaded", () => {
    fetchAndUpdate("/api/v1/status", "vm-status", "VM Status");
    fetchAndUpdate("/api/v1/version", "qemu-version", "QEMU Version");
    fetchAndUpdate("/api/v1/name", "vm-name", "VM Name");
    fetchAndUpdate("/api/v1/uuid", "vm-uuid", "VM UUID");

    fetchAndUpdate("/api/v1/cpus", "cpu-info", "CPU Info");
    fetchAndUpdate("/api/v1/memory", "memory-summary", "Memory Summary");

    fetchAndUpdate("/api/v1/pci", "pci-devices", "PCI Devices");
    fetchAndUpdate("/api/v1/chardev", "char-devices", "Char Devices");

    fetchAndUpdate("/api/v1/block", "block-devices", "Block Devices");

    refreshSnapshots();
});

function fetchAndUpdate(url, elementId, label = "") {
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const el = document.getElementById(elementId);
            el.innerHTML = `<strong>${label}</strong><br><pre>${JSON.stringify(data, null, 2)}</pre>`;
        })
        .catch(err => {
            document.getElementById(elementId).innerHTML = `<strong>${label}</strong><br><span class="text-danger">Error: ${err}</span>`;
        });
}

function refreshSnapshots() {
    fetch("/api/v1/snapshot/list")
        .then(response => response.json())
        .then(data => {
            document.getElementById("snapshots").textContent = data.snapshots || "No snapshots found.";
        })
        .catch(err => {
            document.getElementById("snapshots").textContent = `Error: ${err}`;
        });
}
