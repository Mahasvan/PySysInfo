import builtins
import subprocess

from pysysinfo.dumps.linux.cpu import (
    fetch_cpu_cores,
    fetch_arm_cpu_info,
    fetch_x86_cpu_info,
    fetch_cpu_info,
)
from pysysinfo.models.status_models import PartialStatus, FailedStatus


class TestLinuxCPU:

    def test_fetch_cpu_cores_success(self, monkeypatch):
        output = (
            "# comment\n"
            "0,0,0,0\n"
            "1,0,0,0\n"
            "2,1,0,0\n"
            "3,1,0,0\n"
        )

        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args, 0, stdout=output)

        monkeypatch.setattr(subprocess, "run", mock_run)

        cores = fetch_cpu_cores()
        assert cores == 2

    def test_fetch_cpu_cores_failure(self, monkeypatch):
        def mock_run(*args, **kwargs):
            raise RuntimeError("lscpu failed")

        monkeypatch.setattr(subprocess, "run", mock_run)

        assert fetch_cpu_cores() is None

    def test_fetch_arm_cpu_info_success(self, monkeypatch):
        raw = (
            "processor\t: 0\n"
            "processor\t: 1\n"
            "CPU architecture: 8\n"
            "Hardware\t: BCM2711\n"
        )

        monkeypatch.setattr(
            "pysysinfo.dumps.linux.cpu.fetch_cpu_cores",
            lambda: 4,
        )

        cpu = fetch_arm_cpu_info(raw)

        assert cpu.architecture == "ARM"
        assert cpu.model_name == "BCM2711"
        assert cpu.arch_version == "8"
        assert cpu.threads == 2
        assert cpu.cores == 4
        assert cpu.status.messages == []

    def test_fetch_arm_cpu_info_model_fallback(self, monkeypatch):
        raw = (
            "processor\t: 0\n"
            "CPU architecture: 7\n"
            "Model\t: Raspberry Pi 4\n"
        )

        monkeypatch.setattr("pysysinfo.dumps.linux.cpu.fetch_cpu_cores", lambda: 4)

        cpu = fetch_arm_cpu_info(raw)

        assert cpu.model_name == "Raspberry Pi 4"

    def test_fetch_arm_cpu_info_missing_fields(self, monkeypatch):
        raw = "processor\t: 0\n"

        monkeypatch.setattr("pysysinfo.dumps.linux.cpu.fetch_cpu_cores", lambda: None)

        cpu = fetch_arm_cpu_info(raw)

        assert isinstance(cpu.status, PartialStatus)
        assert cpu.status.messages is not None

    def test_fetch_x86_cpu_info_success(self):
        raw = (
            "processor\t: 0\n"
            "vendor_id\t: GenuineIntel\n"
            "model name\t: Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz\n"
            "flags\t\t: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault pti ssbd ibrs ibpb stibp tpr_shadow flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed adx smap clflushopt intel_pt xsaveopt xsavec xgetbv1 xsaves dtherm arat pln pts hwp hwp_notify hwp_act_window hwp_epp vnmi md_clear flush_l1d arch_capabilities ibpb_exit_to_user\n"
            "cpu cores\t: 2\n"
            "\n"
            "processor\t: 1\n"
            "vendor_id\t: GenuineIntel\n"
            "model name\t: Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz\n"
            "flags\t\t: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault pti ssbd ibrs ibpb stibp tpr_shadow flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed adx smap clflushopt intel_pt xsaveopt xsavec xgetbv1 xsaves dtherm arat pln pts hwp hwp_notify hwp_act_window hwp_epp vnmi md_clear flush_l1d arch_capabilities ibpb_exit_to_user\n"
            "cpu cores\t: 2\n"
        )

        cpu = fetch_x86_cpu_info(raw)

        assert cpu.architecture == "x86"
        assert cpu.model_name == "Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz"
        assert cpu.vendor == "intel"
        assert cpu.bitness == 64
        assert cpu.cores == 2
        assert cpu.threads == 2
        assert "SSE" in cpu.sse_flags
        assert "SSE2" in cpu.sse_flags
        assert "SSE4.1" in cpu.sse_flags
        assert "SSE4.2" in cpu.sse_flags
        assert cpu.status.messages == []

    def test_fetch_x86_cpu_info_missing_fields(self):
        raw = "processor\t: 0\n"

        cpu = fetch_x86_cpu_info(raw)

        assert isinstance(cpu.status, PartialStatus)
        assert cpu.status.messages is not None

    def test_fetch_cpu_info_x86_success(self, monkeypatch):
        raw = "model name\t: Intel CPU\nflags\t\t: lm sse\ncpu cores\t: 4\n\n"

        def mock_open(*args, **kwargs):
            from io import StringIO
            return StringIO(raw)

        monkeypatch.setattr(builtins, "open", mock_open)

        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args, 0, stdout="x86_64")

        monkeypatch.setattr(subprocess, "run", mock_run)

        cpu = fetch_cpu_info()
        assert cpu.architecture == "x86"
        assert cpu.model_name == "Intel CPU"

    def test_fetch_cpu_info_arm_success(self, monkeypatch):
        raw = "Hardware\t: BCM2711\nCPU architecture: 8\nprocessor\t: 0\n"

        def mock_open(*args, **kwargs):
            from io import StringIO
            return StringIO(raw)

        monkeypatch.setattr(builtins, "open", mock_open)

        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args, 0, stdout="aarch64")

        monkeypatch.setattr(subprocess, "run", mock_run)

        monkeypatch.setattr("pysysinfo.dumps.linux.cpu.fetch_cpu_cores", lambda: 4)

        cpu = fetch_cpu_info()
        assert cpu.architecture == "ARM"
        assert cpu.model_name == "BCM2711"

    def test_fetch_cpu_info_failure_file_open(self, monkeypatch):
        def mock_open(*args, **kwargs):
            raise FileNotFoundError("No such file")

        monkeypatch.setattr(builtins, "open", mock_open)

        cpu = fetch_cpu_info()
        assert isinstance(cpu.status, FailedStatus)
        assert cpu.status.messages is not None

    def test_fetch_cpu_info_empty_file(self, monkeypatch):
        def mock_open(*args, **kwargs):
            from io import StringIO
            return StringIO("")

        monkeypatch.setattr(builtins, "open", mock_open)

        cpu = fetch_cpu_info()
        assert isinstance(cpu.status, FailedStatus)
        assert cpu.status.messages is not None


class TestLinuxCPURealWorld:

    def test_fetch_cpu_info_rpi_success(self, monkeypatch):
        with open("tests/assets/raw_cpu_info/rpi.txt", "r") as f:
            raw = f.read()

        def mock_open(*args, **kwargs):
            from io import StringIO
            return StringIO(raw)

        monkeypatch.setattr(builtins, "open", mock_open)

        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args, 0, stdout="aarch64")

        monkeypatch.setattr(subprocess, "run", mock_run)

        monkeypatch.setattr("pysysinfo.dumps.linux.cpu.fetch_cpu_cores", lambda: 4)

        cpu = fetch_cpu_info()
        assert cpu.architecture == "ARM"
        assert cpu.model_name == "Raspberry Pi 4 Model B Rev 1.5"
        assert cpu.arch_version == "8"
        assert cpu.threads == 4
        assert cpu.cores == 4

    def test_fetch_cpu_info_7200u_success(self, monkeypatch):
        with open("tests/assets/raw_cpu_info/7200u.txt", "r") as f:
            raw = f.read()

        def mock_open(*args, **kwargs):
            from io import StringIO
            return StringIO(raw)

        monkeypatch.setattr(builtins, "open", mock_open)

        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args, 0, stdout="x86_64")

        monkeypatch.setattr(subprocess, "run", mock_run)

        cpu = fetch_cpu_info()
        assert cpu.architecture == "x86"
        assert cpu.model_name == "Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz"
        assert cpu.vendor == "intel"
        assert cpu.bitness == 64
        assert cpu.cores == 2
        assert cpu.threads == 4
        assert "SSE4.2" in cpu.sse_flags
