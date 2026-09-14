public class boateye_settings {
    public static void setRegistryValue(String name, String value) throws Exception {
        ProcessBuilder pb = new ProcessBuilder(
            "reg", "add",
            "HKCU\\SOFTWARE\\JavaSoft\\Prefs\\ninjabrainbot",
            "/v", name,
            "/t", "REG_SZ",
            "/d", value,
            "/f"
        );

        pb.inheritIO();
        Process p = pb.start();
        p.waitFor();
    }

    public static void updateSettings() throws Exception {
        setRegistryValue("angle_adjustment_display_type", "1");
        setRegistryValue("angle_adjustment_type", "1");
        setRegistryValue("boat_error", "0.03");
        setRegistryValue("crosshair_correction", "0.0");
        setRegistryValue("default_boat_type", "2");
        setRegistryValue("mc_version", "0");
        setRegistryValue("resolution_height", "16384.0");
        setRegistryValue("sensitivity", "0.02291165");
        setRegistryValue("sigma_boat", "7.0/E-4");
        setRegistryValue("use_precise_angle", "true");
        setRegistryValue("enable_http_server", "true");
        setRegistryValue("use_adv_statistics", "true");
    }

    public static void main(String[] args) throws Exception {
        updateSettings();
    }
}