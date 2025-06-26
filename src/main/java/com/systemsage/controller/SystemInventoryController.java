package com.systemsage.controller;

import com.systemsage.dto.SoftwareInfo;
import com.systemsage.service.SystemInventoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/system-inventory")
public class SystemInventoryController {

    @Autowired
    private SystemInventoryService systemInventoryService;

    @GetMapping
    public List<SoftwareInfo> getInstalledSoftware() {
        return systemInventoryService.getInstalledSoftware();
    }
}
