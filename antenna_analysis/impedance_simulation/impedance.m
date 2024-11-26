%% Important: Read Before Running

% This script computes impedances from scratch which takes a long time for 
% the given data.Only run this when you need to compute the impedance for 
% each frequency from scratch. Otherwise just load the 
% impedance_results_freq_radius.mat file where freq and radius should be 
% replaced with whichever frequency and radius of can you want to load in 
% another script. The command to load the .mat files is below:
% load(filename)
% where filename is the name of the .mat file

load_impedance = 50;
feedWidth = 0.001;
feedOffset = 0.046;
radii = [0.03820, 0.04990, 0.04950, 0.03515, 0.04590];
feedHeights = [0.01, 0.02, 0.03, 0.04, 0.05];
frequencies = [2300, 2300, 2400, 2500, 2500] * 1e6;
freq_ranges = {
    (2070:23:2530) * 1e6, ...
    (2070:23:2530) * 1e6, ...
    (2160:24:2640) * 1e6, ...
    (2250:25:2750) * 1e6, ...
    (2250:25:2750) * 1e6
};

for count = 1:length(frequencies)
    freq = frequencies(count);
    freqGHz = freq / 1e9;
    freqRange = freq_ranges{count};
    radius = radii(count);

    % Preallocate matrices for the current frequency and radius
    numHeights = length(feedHeights);
    numFreqPoints = length(freqRange);
    magnitude = zeros(numHeights, numFreqPoints);
    realPart = zeros(numHeights, numFreqPoints);
    imaginaryPart = zeros(numHeights, numFreqPoints);

    for i = 1:numHeights
        feedHeight = feedHeights(i);

        % Design antenna and calculate impedance
        antennaObject = design(waveguideCircular, freq);
        antennaObject.Radius = radius;
        antennaObject.Height = height;
        antennaObject.FeedHeight = feedHeight;
        antennaObject.FeedWidth = feedWidth;
        antennaObject.FeedOffset = feedOffset;
        antennaObject.Load.Impedance = load_impedance;

        % Calculate impedance for the frequency range
        impedanceData = impedance_each(antennaObject, freqRange);
        magnitude(i, :) = abs(impedanceData);
        realPart(i, :) = real(impedanceData);
        imaginaryPart(i, :) = imag(impedanceData);

        fprintf('Finished processing feed height = %.5f m for frequency = %.1f GHz\n', feedHeight, freqGHz);
    end

    % Save data
    filename = sprintf('impedance_results_%0.1fGHz_%.5f.mat', freqGHz, radius);
    save(filename, 'magnitude', 'realPart', 'imaginaryPart', 'freqRange', 'feedHeights', 'radius', 'freqGHz');
    
    clf;
    plotImpedance(freqRange, magnitude, feedHeights, 'Impedance Magnitude (Ohms)', ...
        sprintf('Impedance vs Frequency (freq = %.1f GHz, radius = %.5f m)', freqGHz, radius));
    filenamePlot = sprintf('Impedance_Magnitude_%0.1fGHz_%.5f.png', freqGHz, radius);
    saveas(gcf, filenamePlot);
    clf;
    plotImpedance(freqRange, realPart, feedHeights, 'Resistance (Ohms)', ...
        sprintf('Resistance vs Frequency (freq = %.1f GHz, radius = %.5f m)', freqGHz, radius));
    filenamePlot = sprintf('Resistance_%0.1fGHz_%.5f.png', freqGHz, radius);
    saveas(gcf, filenamePlot);
    clf;
    plotImpedance(freqRange, imaginaryPart, feedHeights, 'Reactance (Ohms)', ...
        sprintf('Reactance vs Frequency (freq = %.1f GHz, radius = %.5f m)', freqGHz, radius));
    filenamePlot = sprintf('Reactance_%0.1fGHz_%.5f.png', freqGHz, radius);
    saveas(gcf, filenamePlot);

    fprintf('Finished processing all feed heights for frequency = %.1f GHz\n', freqGHz);
end
