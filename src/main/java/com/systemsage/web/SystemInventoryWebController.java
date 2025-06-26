package com.systemsage.web;

import com.systemsage.service.SystemInventoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/system-inventory")
public class SystemInventoryWebController {

    @Autowired
    private SystemInventoryService systemInventoryService;

    @GetMapping
    public String listInstalledSoftware(Model model) {
        model.addAttribute("softwareList", systemInventoryService.getInstalledSoftware());
        return "system-inventory";
    }
}
