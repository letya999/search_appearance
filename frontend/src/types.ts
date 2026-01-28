export interface AttributeScore {
    value: string;
    confidence: number;
}

export interface BasicAttributes {
    gender: AttributeScore;
    age_group: AttributeScore;
    ethnicity: AttributeScore;
    height: AttributeScore;
    body_type: AttributeScore;
}

// Add other sections... for brevity in ID, we map dynamically usually, 
// but let's be explicit for what we display.

export interface PhotoProfile {
    id: string;
    image_path: string;
    basic?: BasicAttributes;
    face?: any;
    hair?: any;
    extra?: any;
    vibe?: any;
    [key: string]: any;
}

export interface SearchResult {
    profile: PhotoProfile;
    score: number;
}

export interface SearchResponse {
    results: SearchResult[];
    analyzed_positives: PhotoProfile[];
    analyzed_negatives: PhotoProfile[];
    target_profile: PhotoProfile;
    execution_time?: number;
}
