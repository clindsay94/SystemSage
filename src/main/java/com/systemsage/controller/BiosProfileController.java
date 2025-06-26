package com.systemsage.controller;

import com.systemsage.entity.BiosProfile;
import com.systemsage.service.BiosProfileService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/bios-profiles")
public class BiosProfileController {

    @Autowired
    private BiosProfileService biosProfileService;

    @GetMapping
    public List<BiosProfile> getAllProfiles() {
        return biosProfileService.getAllProfiles();
    }

    @GetMapping("/{id}")
    public BiosProfile getProfileById(@PathVariable Long id) {
        return biosProfileService.getProfileById(id);
    }

    @PostMapping
    public BiosProfile createProfile(@RequestBody BiosProfile profile) {
        return biosProfileService.saveProfile(profile);
    }

    @PutMapping("/{id}")
    public BiosProfile updateProfile(@PathVariable Long id, @RequestBody BiosProfile profile) {
        profile.setId(id);
        return biosProfileService.saveProfile(profile);
    }

    @DeleteMapping("/{id}")
    public void deleteProfile(@PathVariable Long id) {
        biosProfileService.deleteProfile(id);
    }
}
