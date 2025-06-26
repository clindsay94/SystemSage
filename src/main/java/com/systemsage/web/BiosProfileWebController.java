package com.systemsage.web;

import com.systemsage.entity.BiosProfile;
import com.systemsage.service.BiosProfileService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/bios-profiles")
public class BiosProfileWebController {

    @Autowired
    private BiosProfileService biosProfileService;

    @GetMapping
    public String listProfiles(Model model) {
        model.addAttribute("profiles", biosProfileService.getAllProfiles());
        return "bios-profiles";
    }

    @GetMapping("/new")
    public String newProfileForm(Model model) {
        model.addAttribute("profile", new BiosProfile());
        return "bios-profile-form";
    }

    @PostMapping
    public String saveProfile(BiosProfile profile) {
        biosProfileService.saveProfile(profile);
        return "redirect:/bios-profiles";
    }

    @GetMapping("/edit/{id}")
    public String editProfileForm(@PathVariable Long id, Model model) {
        model.addAttribute("profile", biosProfileService.getProfileById(id));
        return "bios-profile-form";
    }

    @GetMapping("/delete/{id}")
    public String deleteProfile(@PathVariable Long id) {
        biosProfileService.deleteProfile(id);
        return "redirect:/bios-profiles";
    }
}
