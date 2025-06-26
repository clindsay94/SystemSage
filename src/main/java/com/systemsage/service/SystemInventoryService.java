package com.systemsage.service;

import com.systemsage.dto.SoftwareInfo;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

@Service
public class SystemInventoryService {

    public List<SoftwareInfo> getInstalledSoftware() {
        List<SoftwareInfo> softwareList = new ArrayList<>();
        String[] registryPaths = {
                "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                "HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
                "HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        };

        for (String path : registryPaths) {
            try {
                Process process = Runtime.getRuntime().exec("reg query " + path);
                BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
                String line;
                while ((line = reader.readLine()) != null) {
                    if (line.contains(path)) {
                        String key = line.trim();
                        SoftwareInfo softwareInfo = getSoftwareInfo(key);
                        if (softwareInfo != null) {
                            softwareList.add(softwareInfo);
                        }
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        return softwareList;
    }

    private SoftwareInfo getSoftwareInfo(String key) {
        SoftwareInfo softwareInfo = new SoftwareInfo();
        try {
            Process process = Runtime.getRuntime().exec("reg query " + key);
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.contains("DisplayName")) {
                    softwareInfo.setDisplayName(getValue(line));
                } else if (line.contains("DisplayVersion")) {
                    softwareInfo.setDisplayVersion(getValue(line));
                } else if (line.contains("Publisher")) {
                    softwareInfo.setPublisher(getValue(line));
                } else if (line.contains("InstallLocation")) {
                    softwareInfo.setInstallLocation(getValue(line));
                }
            }
        }

        return softwareInfo.getDisplayName() != null ? softwareInfo : null;
    }

    private String getValue(String line) {
        return line.substring(line.indexOf("REG_SZ") + "REG_SZ".length()).trim();
    }
}
