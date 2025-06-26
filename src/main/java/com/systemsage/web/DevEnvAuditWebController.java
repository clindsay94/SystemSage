package com.systemsage.web;

import com.systemsage.service.DevEnvAuditService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/devenv-audit")
public class DevEnvAuditWebController {

    @Autowired
    private DevEnvAuditService devEnvAuditService;

    @GetMapping
    public String audit(Model model) {
        model.addAttribute("components", devEnvAuditService.getDetectedComponents());
        model.addAttribute("envVars", devEnvAuditService.getEnvironmentVariables());
        model.addAttribute("issues", devEnvAuditService.getIdentifiedIssues());
        return "devenv-audit";
    }
}
