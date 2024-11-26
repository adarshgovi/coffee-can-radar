function plotImpedance(freqRange, dataMatrix, feedHeights, ylabelText, titleString)
    figure;
    hold on;
    for i = 1:size(dataMatrix, 1)
        plot(freqRange / 1e6, dataMatrix(i, :), 'DisplayName', ['Feed Height = ', num2str(feedHeights(i)), ' m']);
    end
    hold off;
    xlabel('Frequency (MHz)');
    ylabel(ylabelText);
    title(titleString);
    legend('show');
    grid on;
end