package com.systemsage.service;

import com.systemsage.entity.BiosProfile;
import com.systemsage.repository.BiosProfileRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class BiosProfileService {

    @Autowired
    private BiosProfileRepository biosProfileRepository;

    public List<BiosProfile> getAllProfiles() {
        return biosProfileRepository.findAll();
    }

    public BiosProfile getProfileById(Long id) {
        return biosProfileRepository.findById(id).orElse(null);
    }

    public BiosProfile saveProfile(BiosProfile profile) {
        profile.setLastModifiedDate(LocalDateTime.now());
        return biosProfileRepository.save(profile);
    }

    public void deleteProfile(Long id) {
        biosProfileRepository.deleteById(id);
    }
}
