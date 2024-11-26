function impedanceData = impedance_each(antennaObject, freqRange)
    
    % % Analysis Parameters
    % plotFrequency = frequency;
    % refImpedance = load_impedance;

    % Mesh Generation
    m = mesh(antennaObject, 'MaxEdgeLength',0.01,'MinEdgeLength',0.005,'GrowthRate',0.95);

    impedanceData = impedance(antennaObject, freqRange);

end
