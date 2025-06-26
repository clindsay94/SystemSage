package com.systemsage.controller;

import com.systemsage.service.DevEnvAuditService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/devenv-audit")
public class DevEnvAuditController {

    @Autowired
    private DevEnvAuditService devEnvAuditService;

    @GetMapping("/components")
    public List<String> getDetectedComponents() {
        return devEnvAuditService.getDetectedComponents();
    }

    @GetMapping("/env-vars")
    public List<String> getEnvironmentVariables() {
        return devEnvAuditService.getEnvironmentVariables();
    }

    @GetMapping("/issues")
    public List<String> getIdentifiedIssues() {
        return devEnvAuditService.getIdentifiedIssues();
    }
}
