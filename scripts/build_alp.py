"""
Generates the native AnyLogic 8.8 project file
    anylogic/Kanjurmarg_FOB_Simulation/Kanjurmarg_FOB_Simulation.alp

The XML element structure follows real AnyLogic 8.8.3 project files (AlpVersion 8.8.3).
engine/FobEngine.java is embedded verbatim as Main's "Additional class code", so the model
runs exactly the same stochastic logic that produced the CSV results.

    python3 scripts/build_alp.py
"""
import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_NAME = "Kanjurmarg_FOB_Simulation"
PKG = "kanjurmarg_fob_simulation"
OUT_DIR = os.path.join(ROOT, "anylogic", MODEL_NAME)

_next_id = [1761530000000]


def nid():
    _next_id[0] += 1
    return _next_id[0]


def cdata(s):
    return "<![CDATA[" + s.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def argb(hex_rgb, alpha=255):
    """'#RRGGBB' -> AnyLogic signed 32-bit ARGB integer."""
    h = hex_rgb.lstrip("#")
    v = (alpha << 24) | int(h, 16)
    return v - (1 << 32) if v >= (1 << 31) else v


# ------------------------------------------------------------------ palette
C = dict(
    bg="#F4F6F9", ink="#1F2933", muted="#5F6B7A", faint="#9AA5B1", card="#FFFFFF", cardline="#DCE1E8",
    platform="#D5DAE1", platform_edge="#B8C0CA", track="#7B8794", rail="#52606D", concourse="#E9EDF2",
    street="#CBD2D9", teal="#00A19B", teal_soft="#CDEDEC", blue="#2563EB", blue_soft="#DCE7FD",
    red="#D93025", red_soft="#FBE2E0", amber="#D97706", amber_soft="#FCEBD0", east="#EEF0F3",
)

PX_PER_M = 8.0
OX, OY = 40, 150     # pixel origin of the station layout (metres -> pixels)


def X(m):
    return OX + m * PX_PER_M


def Y(m):
    return OY + m * PX_PER_M


# ------------------------------------------------------------------ shape helpers
def common(name, x, y, public=True):
    return (f"<Id>{nid()}</Id><Name>{cdata(name)}</Name><X>{x:g}</X><Y>{y:g}</Y>"
            f"<Label><X>10</X><Y>0</Y></Label><PublicFlag>{'true' if public else 'false'}</PublicFlag>"
            f"<PresentationFlag>true</PresentationFlag><ShowLabel>false</ShowLabel>")


_shape_n = [0]


def sname(prefix):
    _shape_n[0] += 1
    return f"{prefix}{_shape_n[0]}"


def rect(x, y, w, h, fill=None, line=None, lw=1, name=None, style="SOLID"):
    name = name or sname("rect_")
    return (f"<Rectangle>{common(name, x, y)}<DrawMode>SHAPE_DRAW_2D</DrawMode><EmbeddedIcon>false</EmbeddedIcon>"
            f"<Z>0</Z><ZHeight>10</ZHeight><LineWidth>{lw:g}</LineWidth>"
            f"{'<LineColor/>' if line is None else f'<LineColor>{argb(line)}</LineColor>'}"
            f"<LineMaterial>null</LineMaterial><LineStyle>{style}</LineStyle><Width>{w:g}</Width><Height>{h:g}</Height>"
            f"<Rotation>0.0</Rotation>{'<FillColor/>' if fill is None else f'<FillColor>{argb(fill)}</FillColor>'}"
            f"<FillMaterial>null</FillMaterial></Rectangle>")


def poly(points, line, lw=1, closed=False, fill=None, name=None, style="SOLID"):
    name = name or sname("line_")
    x0, y0 = points[0]
    pts = "".join(f"<Point><X>{px - x0:g}</X><Y>{py - y0:g}</Y><Z>0</Z></Point>" for px, py in points)
    return (f"<Polyline>{common(name, x0, y0)}<DrawMode>SHAPE_DRAW_2D</DrawMode><EmbeddedIcon>false</EmbeddedIcon>"
            f"<Z>0</Z><ZHeight>10</ZHeight><LineWidth>{lw:g}</LineWidth><LineColor>{argb(line)}</LineColor>"
            f"<LineMaterial>null</LineMaterial><LineStyle>{style}</LineStyle><BeginArrowSize>1</BeginArrowSize>"
            f"<BeginArrowStyle>0</BeginArrowStyle><EndArrowSize>1</EndArrowSize><EndArrowStyle>0</EndArrowStyle>"
            f"{'<FillColor/>' if fill is None else f'<FillColor>{argb(fill)}</FillColor>'}<FillMaterial>null</FillMaterial>"
            f"<Points>{pts}</Points><Closed>{'true' if closed else 'false'}</Closed></Polyline>")


def text(x, y, s, size=12, color="ink", bold=False, align="LEFT", code=None, name=None, font="SansSerif"):
    name = name or sname("text_")
    return (f"<Text>{common(name, x, y)}<DrawMode>SHAPE_DRAW_2D</DrawMode><EmbeddedIcon>false</EmbeddedIcon><Z>0</Z>"
            f"<Rotation>0.0</Rotation><Color>{argb(C.get(color, color))}</Color><Text>{cdata(s)}</Text>"
            f"{'' if code is None else f'<TextCode>{cdata(code)}</TextCode>'}"
            f"<Font><Name>{font}</Name><Size>{size}</Size><Style>{1 if bold else 0}</Style></Font>"
            f"<Alignment>{align}</Alignment></Text>")


def oval(x, y, r, fill, fill_code=None, name=None, line=None):
    name = name or sname("oval_")
    return (f"<Oval>{common(name, x, y)}<DrawMode>SHAPE_DRAW_2D</DrawMode><EmbeddedIcon>false</EmbeddedIcon><Z>0</Z>"
            f"<ZHeight>10</ZHeight><LineWidth>1</LineWidth>"
            f"{'<LineColor/>' if line is None else f'<LineColor>{argb(line)}</LineColor>'}"
            f"<LineMaterial>null</LineMaterial><LineStyle>SOLID</LineStyle><RadiusX>{r:g}</RadiusX><RadiusY>{r:g}</RadiusY>"
            f"<Rotation>0.0</Rotation><FillColor>{argb(fill)}</FillColor>"
            f"{'' if fill_code is None else f'<FillColorCode>{cdata(fill_code)}</FillColorCode>'}"
            f"<FillMaterial>null</FillMaterial></Oval>")


def button(x, y, w, h, label, action, name):
    return (f"<Control Type=\"Button\"><EmbeddedIcon>false</EmbeddedIcon>{common(name, x, y)}"
            f"<DrawMode>SHAPE_DRAW_2D3D</DrawMode><BasicProperties Width=\"{w}\" Height=\"{h}\">"
            f"<EmbeddedIcon>false</EmbeddedIcon><TextColor/><Enabled>true</Enabled><ActionCode>{cdata(action)}</ActionCode>"
            f"</BasicProperties><ExtendedProperties><Font Name=\"Dialog\" Size=\"12\" Style=\"1\"/>"
            f"<LabelText>{cdata(label)}</LabelText></ExtendedProperties></Control>")


def card(x, y, w, h, accent=None):
    out = rect(x, y, w, h, fill=C["card"], line=C["cardline"], lw=1)
    if accent:
        out += rect(x, y, 5, h, fill=accent, line=None, lw=0)
    return out


# ------------------------------------------------------------------ model-level helpers
def time_unit(code, unit="SECOND"):
    return f"<Code>{cdata(code)}</Code><Unit Class=\"TimeUnits\">{cdata(unit)}</Unit>"


def agent_header(class_id, name, gen_id, extra=""):
    return f"""
		<ActiveObjectClass>
			<Id>{class_id}</Id>
			<Name>{cdata(name)}</Name>
			{extra}
			<Generic>false</Generic>
			<GenericParameter>
				<Id>{gen_id}</Id>
				<Name>{cdata(str(gen_id))}</Name>
				<GenericParameterValue Class="CodeValue">
					<Code>{cdata('T extends Agent')}</Code>
				</GenericParameterValue>
				<GenericParameterLabel>{cdata('Generic parameter:')}</GenericParameterLabel>
			</GenericParameter>
			<FlowChartsUsage>ENTITY</FlowChartsUsage>
			<SamplesToKeep>100</SamplesToKeep>
			<LimitNumberOfArrayElements>false</LimitNumberOfArrayElements>
			<ElementsLimitValue>100</ElementsLimitValue>
			<MakeDefaultViewArea>true</MakeDefaultViewArea>
			<SceneGridColor/>
			<SceneBackgroundColor/>
			<SceneSkybox>null</SceneSkybox>"""


def agent_props(speed="1.3"):
    return f"""
			<AgentProperties>
				<EnvironmentDefinesInitialLocation>true</EnvironmentDefinesInitialLocation>
				<RotateAnimationTowardsMovement>false</RotateAnimationTowardsMovement>
				<RotateAnimationVertically>false</RotateAnimationVertically>
				<VelocityCode Class="CodeUnitValue">
					<Code>{cdata(speed)}</Code>
					<Unit Class="SpeedUnits">{cdata('MPS')}</Unit>
				</VelocityCode>
				<PhysicalLength Class="CodeUnitValue">
					<Code>{cdata('0.5')}</Code>
					<Unit Class="LengthUnits">{cdata('METER')}</Unit>
				</PhysicalLength>
				<PhysicalWidth Class="CodeUnitValue">
					<Code>{cdata('0.5')}</Code>
					<Unit Class="LengthUnits">{cdata('METER')}</Unit>
				</PhysicalWidth>
				<PhysicalHeight Class="CodeUnitValue">
					<Code>{cdata('1.7')}</Code>
					<Unit Class="LengthUnits">{cdata('METER')}</Unit>
				</PhysicalHeight>
			</AgentProperties>"""


def env_props(width, height, layout="USER_DEF"):
    return f"""
			<EnvironmentProperties>
					<EnableSteps>false</EnableSteps>
					<StepDurationCode Class="CodeUnitValue">
						{time_unit('1.0')}
					</StepDurationCode>
					<SpaceType>CONTINUOUS</SpaceType>
					<WidthCode>{cdata(str(width))}</WidthCode>
					<HeightCode>{cdata(str(height))}</HeightCode>
					<ZHeightCode>{cdata('0')}</ZHeightCode>
					<ColumnsCountCode>{cdata('100')}</ColumnsCountCode>
					<RowsCountCode>{cdata('100')}</RowsCountCode>
					<NeigborhoodType>MOORE</NeigborhoodType>
					<LayoutType>{layout}</LayoutType>
					<LayoutTypeApplyOnStartup>true</LayoutTypeApplyOnStartup>
					<NetworkType>USER_DEF</NetworkType>
					<NetworkTypeApplyOnStartup>true</NetworkTypeApplyOnStartup>
					<ConnectionsPerAgentCode>{cdata('2')}</ConnectionsPerAgentCode>
					<ConnectionsRangeCode>{cdata('50')}</ConnectionsRangeCode>
					<NeighborLinkFractionCode>{cdata('0.95')}</NeighborLinkFractionCode>
					<MCode>{cdata('10')}</MCode>
			</EnvironmentProperties>
			<DatasetsCreationProperties>
				<AutoCreate>false</AutoCreate>
					<OccurrenceAtTime>true</OccurrenceAtTime>
					<OccurrenceDate>1761535800000</OccurrenceDate>
					<OccurrenceTime Class="CodeUnitValue">
						{time_unit('0')}
					</OccurrenceTime>
					<RecurrenceCode Class="CodeUnitValue">
						{time_unit('1')}
					</RecurrenceCode>
			</DatasetsCreationProperties>"""


def scale_ruler(inherited):
    return f"""
			<ScaleRuler>
				<Id>{nid()}</Id>
				<Name>{cdata('scale')}</Name>
				<X>{OX}</X><Y>{OY - 40}</Y>
				<PublicFlag>false</PublicFlag>
				<PresentationFlag>false</PresentationFlag>
				<ShowLabel>false</ShowLabel>
				<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
				<Length>80</Length>
				<Rotation>0</Rotation>
				<ScaleType>BASED_ON_LENGTH</ScaleType>
				<ModelLength>10</ModelLength>
				<LengthUnits>METER</LengthUnits>
				<Scale>8</Scale>
				<InheritedFromParentAgentType>{'true' if inherited else 'false'}</InheritedFromParentAgentType>
			</ScaleRuler>"""


def parameter(name, typ, default, x, y, label):
    return f"""
				<Variable Class="Parameter">
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<Properties SaveInSnapshot="true" ModificatorType="STATIC">
						<Type>{cdata(typ)}</Type>
						<UnitType>{cdata('NONE')}</UnitType>
						<SdArray>false</SdArray>
						<DefaultValue Class="CodeValue">
							<Code>{cdata(default)}</Code>
						</DefaultValue>
						<ParameterEditor>
							<Id>{nid()}</Id>
							<Label>{cdata(label)}</Label>
							<EditorContolType>TEXT_BOX</EditorContolType>
							<MinSliderValue>{cdata('0')}</MinSliderValue>
							<MaxSliderValue>{cdata('100')}</MaxSliderValue>
							<DelimeterType>NO_DELIMETER</DelimeterType>
						</ParameterEditor>
					</Properties>
				</Variable>"""


def plain_var(name, typ, init, x, y, public=True):
    init_xml = "" if init is None else f"""
						<InitialValue Class="CodeValue">
							<Code>{cdata(init)}</Code>
						</InitialValue>"""
    return f"""
				<Variable Class="PlainVariable">
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<Properties SaveInSnapshot="true" Constant="false" AccessType="public" StaticVariable="false">
						<Type>{cdata(typ)}</Type>{init_xml}
					</Properties>
				</Variable>"""


def function(name, ret, body, x, y, params=(), returns=False):
    p = "".join(f"<Parameter><Name>{cdata(n)}</Name><Type>{cdata(t)}</Type></Parameter>" for n, t in params)
    return f"""
				<Function AccessType="default" StaticFunction="false">
					<ReturnModificator>{'RETURNS_VALUE' if returns else 'VOID'}</ReturnModificator>
					<ReturnType>{cdata(ret)}</ReturnType>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					{p}
					<Body>{cdata(body)}</Body>
				</Function>"""


def dynamic_event(name, params, action, x, y):
    p = "".join(f"<Parameter><Name>{cdata(n)}</Name><Type>{cdata(t)}</Type></Parameter>" for n, t in params)
    return f"""
				<DynamicEventClass>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					{p}
					<Action>{cdata(action)}</Action>
				</DynamicEventClass>"""


def cyclic_event(name, first, period, action, x, y):
    return f"""
				<Event>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<Properties TriggerType="timeout" Mode="cyclic">
						<Timeout Class="CodeUnitValue">
							{time_unit(period)}
						</Timeout>
						<Rate Class="CodeUnitValue">
							<Code>{cdata('1')}</Code>
							<Unit Class="RateUnits">{cdata('PER_SECOND')}</Unit>
						</Rate>
						<OccurrenceAtTime>true</OccurrenceAtTime>
						<OccurrenceDate>1761535860000</OccurrenceDate>
						<OccurrenceTime Class="CodeUnitValue">
							{time_unit(first)}
						</OccurrenceTime>
						<RecurrenceCode Class="CodeUnitValue">
							{time_unit(period)}
						</RecurrenceCode>
						<Condition>{cdata('false')}</Condition>
					</Properties>
					<Action>{cdata(action)}</Action>
				</Event>"""


def histogram_data(name, x, y):
    return f"""
				<HistogramData>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>15</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<AutoUpdate>false</AutoUpdate>
					<OccurrenceAtTime>true</OccurrenceAtTime>
					<OccurrenceDate>1761535800000</OccurrenceDate>
					<OccurrenceTime Class="CodeUnitValue">
						{time_unit('0')}
					</OccurrenceTime>
					<RecurrenceCode Class="CodeUnitValue">
						{time_unit('60')}
					</RecurrenceCode>
					<Value>{cdata('')}</Value>
					<NumberOfIntervals>16</NumberOfIntervals>
					<MinMaxAutodetect>false</MinMaxAutodetect>
					<RangeMinExpression>{cdata('0')}</RangeMinExpression>
					<RangeMaxExpression>{cdata('40')}</RangeMaxExpression>
					<InitialIntervalSize>{cdata('2.5')}</InitialIntervalSize>
					<CalculateCDF>false</CalculateCDF>
					<CalculatePercentiles>false</CalculatePercentiles>
					<LowPercent>10</LowPercent>
					<HighPercent>10</HighPercent>
					<Title>{cdata(name)}</Title>
				</HistogramData>"""


def chart_frame(w, h, xoff, yoff, cw, ch):
    return f"""<EmbeddedIcon>false</EmbeddedIcon>
					<Width>{w}</Width>
					<Height>{h}</Height>
					<BackgroundColor/>
					<BorderColor/>
					<ChartArea>
						<XOffset>{xoff}</XOffset>
						<YOffset>{yoff}</YOffset>
						<Width>{cw}</Width>
						<Height>{ch}</Height>
						<BackgroundColor>{argb('#FFFFFF')}</BackgroundColor>
						<BorderColor>{argb(C['cardline'])}</BorderColor>
						<GridColor>{argb('#E4E7EB')}</GridColor>
					</ChartArea>
					<Legend>
						<Place>SOUTH</Place>
						<TextColor>{argb(C['muted'])}</TextColor>
						<Size>22</Size>
					</Legend>
					<Labels>
						<HorLabelsPosition>DEFAULT</HorLabelsPosition>
						<VerLabelsPosition>DEFAULT</VerLabelsPosition>
						<TextColor>{argb(C['muted'])}</TextColor>
					</Labels>
					<ShowLegend>true</ShowLegend>"""


def time_plot(name, x, y, w, h, series, vmax):
    ds = ""
    for title, expr, col in series:
        ds += f"""
					<DatasetExpression>
						<Title>{cdata(title)}</Title>
					<Id>{nid()}</Id>
					<Expression>{cdata('ds_' + expr)}</Expression>
					<Color>{argb(col)}</Color>
					<Expression2>{cdata(expr)}</Expression2>
					<Expression2Flag>true</Expression2Flag>
						<PointStyle>NONE</PointStyle>
						<LineWidth>2.0</LineWidth>
					</DatasetExpression>"""
    return f"""
    			<TimePlot>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>0</X><Y>-10</Y></Label>
					<PublicFlag>true</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>false</ShowLabel>
					<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
					<AutoUpdate>true</AutoUpdate>
					<OccurrenceAtTime>true</OccurrenceAtTime>
					<OccurrenceDate>1761535860000</OccurrenceDate>
					<OccurrenceTime Class="CodeUnitValue">
						{time_unit('60.5')}
					</OccurrenceTime>
					<RecurrenceCode Class="CodeUnitValue">
						{time_unit('60')}
					</RecurrenceCode>
					{chart_frame(w, h, 40, 10, w - 60, h - 60)}
					<TimeWindowsMovementType>MOVEMENT_WITH_TIME</TimeWindowsMovementType>
					<TimeWindowUnits>DAY</TimeWindowUnits>
					<VerScaleFromExpression>{cdata('0')}</VerScaleFromExpression>
					<VerScaleToExpression>{cdata(str(vmax))}</VerScaleToExpression>
					<VerScaleType>FIXED</VerScaleType>
					<DrawLine>true</DrawLine>
					<Interpolation>LINEAR</Interpolation>{ds}
					<SamplesToKeep>200</SamplesToKeep>
					<TimeWindowExpression>{cdata('1.0 / 24.0')}</TimeWindowExpression>
					<FillAreaUnderLine>false</FillAreaUnderLine>
					<LabelFormat>MODEL_DATE_TIME_ONLY</LabelFormat>
    			</TimePlot>"""


def histogram_chart(name, x, y, w, h, series):
    ds = ""
    for title, data, col in series:
        ds += f"""
					<HistogramDataExpression>
					<Id>{nid()}</Id>
					<Expression>{cdata(data)}</Expression>
						<ColorPDF>{argb(col)}</ColorPDF>
						<ColorCDF>{argb(C['muted'])}</ColorCDF>
						<ColorLowPercent>{argb(C['faint'])}</ColorLowPercent>
						<ColorHighPercent>{argb(C['faint'])}</ColorHighPercent>
						<ColorMean>{argb(C['ink'])}</ColorMean>
						<LineWidth>1</LineWidth>
						<Title>{cdata(title)}</Title>
					</HistogramDataExpression>"""
    return f"""
    			<Histogram>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>0</X><Y>-10</Y></Label>
					<PublicFlag>true</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>false</ShowLabel>
					<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
					<AutoUpdate>true</AutoUpdate>
					<OccurrenceAtTime>true</OccurrenceAtTime>
					<OccurrenceDate>1761535860000</OccurrenceDate>
					<OccurrenceTime Class="CodeUnitValue">
						{time_unit('60.5')}
					</OccurrenceTime>
					<RecurrenceCode Class="CodeUnitValue">
						{time_unit('60')}
					</RecurrenceCode>
					{chart_frame(w, h, 40, 10, w - 60, h - 60)}
					<ShowPDF>true</ShowPDF>
					<ShowCDF>false</ShowCDF>
					<ShowMean>true</ShowMean>
					<Bars>
						<Direction>UP</Direction>
						<RelativeWidth>0.8</RelativeWidth>
					</Bars>{ds}
    			</Histogram>"""


def edit_box(x, y, w, link, name, minv=None, maxv=None):
    lim = ""
    if minv is not None:
        lim += f"<MinValue>{cdata(str(minv))}</MinValue>"
    if maxv is not None:
        lim += f"<MaxValue>{cdata(str(maxv))}</MaxValue>"
    return (f"<Control Type=\"EditBox\"><EmbeddedIcon>false</EmbeddedIcon>{common(name, x, y)}"
            f"<DrawMode>SHAPE_DRAW_2D3D</DrawMode><BasicProperties Width=\"{w}\" Height=\"28\">"
            f"<EmbeddedIcon>false</EmbeddedIcon><FillColor/><TextColor/><Enabled>true</Enabled></BasicProperties>"
            f"<ExtendedProperties><Font Name=\"Dialog\" Size=\"12\" Style=\"0\"/>{lim}<LinkTo>true</LinkTo>"
            f"<Link>{link}</Link></ExtendedProperties></Control>")


def radio(x, y, w, h, buttons, link, name):
    b = "".join(f"<Button>{cdata(s)}</Button>" for s in buttons)
    return (f"<Control Type=\"RadioButtons\"><EmbeddedIcon>false</EmbeddedIcon>{common(name, x, y)}"
            f"<DrawMode>SHAPE_DRAW_2D3D</DrawMode><BasicProperties Width=\"{w}\" Height=\"{h}\">"
            f"<EmbeddedIcon>false</EmbeddedIcon><TextColor/><Enabled>true</Enabled></BasicProperties>"
            f"<ExtendedProperties><Font Name=\"Dialog\" Size=\"13\" Style=\"0\"/><DefaultValueCode>{cdata('0')}</DefaultValueCode>"
            f"<Orientation>VERTICAL</Orientation>{b}<LinkTo>true</LinkTo><Link>{link}</Link></ExtendedProperties></Control>")


# ==================================================================================================
# Java code of the model
# ==================================================================================================
ENGINE_SRC = open(os.path.join(ROOT, "engine", "FobEngine.java"), encoding="utf-8").read()

MAIN_ADDITIONAL = ENGINE_SRC + """

// ---- colours shared by Main and Passenger -------------------------------------------------
public static final Color C_PF1 = new Color(0xD9, 0x77, 0x06);   // amber  — direct PF1 route
public static final Color C_FOB2 = new Color(0x00, 0xA1, 0x9B);  // teal   — FOB 2
public static final Color C_FOB3 = new Color(0x25, 0x63, 0xEB);  // blue   — FOB 3
public static final Color C_OK = new Color(0x00, 0xA1, 0x9B);
public static final Color C_WARN = new Color(0xD9, 0x77, 0x06);
public static final Color C_HIGH = new Color(0xD9, 0x30, 0x25);
"""

STARTUP = """// ---------------------------------------------------------------------
// Start-up: one independent random stream per arrival stream, first arrivals scheduled.
// The same seed rule is used by FobEngine.runReplication, so this animated run is
// identical to replication 1 of the batch (seed = randomSeed).
// ---------------------------------------------------------------------
streamRng = new java.util.Random[FobEngine.NUM_STREAMS];
fob2PerMin = new int[durationMin];
fob3PerMin = new int[durationMin];
for (int s = 0; s < FobEngine.NUM_STREAMS; s++) {
	streamRng[s] = FobEngine.newStreamRandom(randomSeed, s);
	double lambda = FobEngine.baseRatePerMin(s) * demandMultiplier;
	create_Arrival(FobEngine.drawInterarrivalSec(streamRng[s], lambda), s);
}
updateRouteSplitBars();
traceln("Kanjurmarg FOB model started: scenario %s (x%.2f), seed %d, %d min", scenarioName, demandMultiplier, randomSeed, durationMin);"""

FN_ROUTE_PROBS = """// Configured route probabilities (Direct PF1, FOB 2, FOB 3). FOB 1 is closed and has no entry.
double[] p = {pDirectPF1, pFOB2, pFOB3};
double sum = p[0] + p[1] + p[2];
if (Math.abs(sum - 1.0) > 1e-9) {          // normalise if the user typed shares that do not add to 1
	for (int i = 0; i < 3; i++) p[i] = p[i] / sum;
}
return p;"""

FN_SPAWN = """// Create one passenger of the given stream on the chosen route and start walking.
int entrance = FobEngine.entranceOf(stream);
boolean entering = FobEngine.isEntering(stream);
Passenger p = add_passengers();
p.routeIdx = route;
p.entering = entering;
p.entrance = entrance;
p.wpPath = FobEngine.waypoints(entrance, entering, route);
p.wpIndex = 0;
p.jumpTo(toPxX(p.wpPath[0][0]), toPxY(p.wpPath[0][1]));
p.setSpeed(walkSpeed, MPS);

generated++;
routeCount[route]++;
if (route != FobEngine.ROUTE_PF1) {
	// the crossing is counted once, when the passenger reaches the FOB deck mid-point
	create_Crossing(FobEngine.crossingDelaySec(entrance, entering, route, walkSpeed), route);
}
advance(p);"""

FN_ADVANCE = """// Send the passenger to its next way-point, or remove it when the path is finished.
if (p.wpIndex >= p.wpPath.length - 1) {
	completed++;
	remove_passengers(p);
	return;
}
double[] a = p.wpPath[p.wpIndex];
double[] b = p.wpPath[p.wpIndex + 1];
p.moveTo(toPxX(b[0]), toPxY(b[1]));
create_Waypoint(FobEngine.segmentLength(a, b) / walkSpeed, p);"""

FN_TOPX = "return %g + xMetres * %g;" % (OX, PX_PER_M)
FN_TOPY = "return %g + yMetres * %g;" % (OY, PX_PER_M)

FN_CAP2 = "return FobEngine.capacityPerMin(fob2Width, flowIntensity);"
FN_CAP3 = "return FobEngine.capacityPerMin(fob3Width, flowIntensity);"

FN_UTILCOLOR = """// Traffic-light colour for a utilization value (% of reference capacity)
if (u < 50) return C_OK;
if (u < 80) return C_WARN;
return C_HIGH;"""

FN_ROUTEBARS = """// Route-split display: bar lengths proportional to the configured probabilities
double[] p = routeProbs();
double full = 250;
barRoutePF1.setWidth(full * p[0]);
barRouteFOB2.setWidth(full * p[1]);
barRouteFOB3.setWidth(full * p[2]);"""

EV_ARRIVAL = """// Poisson arrival for stream 'stream': create the passenger, then schedule the next arrival.
if (time() >= durationMin * 60.0) return;            // arrivals stop at the end of the run
int route = FobEngine.drawRoute(streamRng[stream], routeProbs());
spawnPassenger(stream, route);
double lambda = FobEngine.baseRatePerMin(stream) * demandMultiplier;
create_Arrival(FobEngine.drawInterarrivalSec(streamRng[stream], lambda), stream);"""

EV_WAYPOINT = """p.wpIndex++;
p.jumpTo(toPxX(p.wpPath[p.wpIndex][0]), toPxY(p.wpPath[p.wpIndex][1]));
advance(p);"""

EV_CROSSING = """// Count one FOB crossing in the one-minute interval in which it happens.
int minute = (int) Math.floor(time() / 60.0);
if (minute >= durationMin) return;
if (route == FobEngine.ROUTE_FOB2) { fob2PerMin[minute]++; fob2Total++; }
else if (route == FobEngine.ROUTE_FOB3) { fob3PerMin[minute]++; fob3Total++; }
else { fob1Total++; }   // unreachable: FOB 1 is closed (kept as an explicit check)"""

EV_MINUTE = """// Close the one-minute interval that has just ended and update the dashboard.
int m = (int) Math.round(time() / 60.0) - 1;
if (m < 0 || m >= durationMin) return;
lastFlow2 = fob2PerMin[m];
lastFlow3 = fob3PerMin[m];
lastU2 = lastFlow2 / capacity2() * 100.0;
lastU3 = lastFlow3 / capacity3() * 100.0;
peakU2 = Math.max(peakU2, lastU2);
peakU3 = Math.max(peakU3, lastU3);
sumU2 += lastU2;
sumU3 += lastU3;
minutesDone = m + 1;
utilHist2.add(lastU2);
utilHist3.add(lastU3);

// live utilization bars (full bar = 50% of reference capacity)
double full = 250;
barU2.setWidth(Math.min(full, full * lastU2 / 50.0));
barU3.setWidth(Math.min(full, full * lastU3 / 50.0));
barU2.setFillColor(utilColor(lastU2));
barU3.setFillColor(utilColor(lastU3));

if (minutesDone >= durationMin) {
	runFinished = true;
	traceln("Run complete: FOB2 %d crossings (%.2f pax/min), FOB3 %d crossings (%.2f pax/min), FOB1 %d",
		fob2Total, fob2Total / (double) durationMin, fob3Total, fob3Total / (double) durationMin, fob1Total);
	getEngine().pause();
}"""

FN_BATCH = """// -----------------------------------------------------------------------------------------
// Batch experiment: 'replications' independent replications for each demand scenario
// (x1.00, x1.10, x1.20), seeds randomSeed .. randomSeed+replications-1 (common random numbers).
// Uses exactly the same FobEngine code as the animation. Writes anylogic_batch_results.csv.
// -----------------------------------------------------------------------------------------
double[] mults = {1.00, 1.10, 1.20};
String[] names = {"Baseline", "+10%", "+20%"};
double[] p = routeProbs();
double c2 = capacity2(), c3 = capacity3();
StringBuilder sb = new StringBuilder();
sb.append(String.format("%-9s %-6s %8s %8s %8s %8s %8s%n", "Scenario", "FOB", "Flow", "+-95%CI", "U mean", "U p95", "U max"));
java.io.PrintWriter out = null;
try {
	out = new java.io.PrintWriter("anylogic_batch_results.csv");
	out.println("scenario,multiplier,replication,seed,facility,crossings,mean_flow_pax_per_min,mean_util_pct,p95_util_pct,max_util_pct,direct_pf1_passengers,fob1_crossings");
} catch (Exception e) {
	traceln("Could not open CSV file for writing: " + e);
}
for (int k = 0; k < 3; k++) {
	double[][] flow = new double[2][replications];
	double[][] umean = new double[2][replications];
	double[][] up95 = new double[2][replications];
	double[][] umax = new double[2][replications];
	for (int r = 0; r < replications; r++) {
		long seed = randomSeed + r;
		FobEngine.Result res = FobEngine.runReplication(seed, mults[k], p, durationMin, 0, walkSpeed);
		for (int f = 0; f < 2; f++) {
			int[] perMin = (f == 0) ? res.fob2PerMinute : res.fob3PerMinute;
			double cap = (f == 0) ? c2 : c3;
			double[] u = new double[perMin.length];
			int total = 0;
			for (int i = 0; i < perMin.length; i++) { u[i] = perMin[i] / cap * 100.0; total += perMin[i]; }
			flow[f][r] = total / (double) durationMin;
			umean[f][r] = FobEngine.mean(u);
			up95[f][r] = FobEngine.percentile(u, 95);
			double mx = 0; for (double v : u) mx = Math.max(mx, v);
			umax[f][r] = mx;
			if (out != null) {
				out.println(String.format(java.util.Locale.ROOT, "%s,%.2f,%d,%d,%s,%d,%.4f,%.4f,%.4f,%.4f,%d,%d",
					names[k], mults[k], r + 1, seed, f == 0 ? "FOB 2" : "FOB 3", total, flow[f][r],
					umean[f][r], up95[f][r], umax[f][r], res.routeTotal(FobEngine.ROUTE_PF1), res.fob1Crossings));
			}
		}
	}
	for (int f = 0; f < 2; f++) {
		double ci = FobEngine.t95(replications - 1) * FobEngine.sampleStdDev(flow[f]) / Math.sqrt(replications);
		batchMeanU[k][f] = FobEngine.mean(umean[f]);
		batchP95U[k][f] = FobEngine.mean(up95[f]);
		sb.append(String.format("%-9s %-6s %8.2f %8.2f %7.2f%% %7.2f%% %7.2f%%%n", names[k], f == 0 ? "FOB 2" : "FOB 3",
			FobEngine.mean(flow[f]), ci, batchMeanU[k][f], batchP95U[k][f], FobEngine.mean(umax[f])));
	}
}
if (out != null) out.close();
batchSummary = sb.toString();
batchDone = true;

// scenario-comparison bars (height 150 px = 40 % utilization)
ShapeRectangle[][] bars = {{cmpBar_b2, cmpBar_b3}, {cmpBar_p2, cmpBar_p3}, {cmpBar_q2, cmpBar_q3}};
for (int k = 0; k < 3; k++) {
	for (int f = 0; f < 2; f++) {
		double h = Math.min(150, 150 * batchMeanU[k][f] / 40.0);
		bars[k][f].setHeight(h);
		bars[k][f].setY(cmpBaseY - h);
	}
}
traceln(batchSummary);"""

PASSENGER_CLASS_ID = nid()
PASSENGER_GEN_ID = nid()
MAIN_CLASS_ID = nid()
MAIN_GEN_ID = nid()


def passenger_class():
    lvl = nid()
    pres = oval(0, 0, 3.2, C["teal"],
                fill_code="routeIdx == 0 ? Main.C_PF1 : (routeIdx == 1 ? Main.C_FOB2 : Main.C_FOB3)",
                name="body", line="#FFFFFF")
    return agent_header(PASSENGER_CLASS_ID, "Passenger", PASSENGER_GEN_ID) + agent_props() + env_props(500, 500) + \
        scale_ruler(True) + f"""
			<CurrentLevel>{lvl}</CurrentLevel>
			<ConnectionsId>{nid()}</ConnectionsId>
			<Variables>""" + \
        plain_var("routeIdx", "int", "0", 50, 50) + \
        plain_var("entering", "boolean", "true", 50, 80) + \
        plain_var("entrance", "int", "0", 50, 110) + \
        plain_var("wpPath", "double[][]", None, 50, 140) + \
        plain_var("wpIndex", "int", "0", 50, 170) + f"""
			</Variables>
			<ContainerLinks>
				<ContainerLink>
					<Id>{nid()}</Id>
					<Name>{cdata('main')}</Name>
					<X>200</X><Y>50</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<ActiveObjectClass>
						<PackageName>{cdata(PKG)}</PackageName>
						<ClassName>{cdata('Main')}</ClassName>
					</ActiveObjectClass>
				</ContainerLink>
			</ContainerLinks>
			<Presentation>
				<Level>
					<Id>{lvl}</Id>
					<Name>{cdata('level')}</Name>
					<X>0</X><Y>0</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>true</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>false</ShowLabel>
					<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
					<Z>0</Z>
					<LevelVisibility>DIM_NON_CURRENT</LevelVisibility>
			<Presentation>
				{pres}
			</Presentation>
				</Level>
			</Presentation>
		</ActiveObjectClass>"""


# ------------------------------------------------------------------ station layout (pixels)
def layout_shapes():
    s = []
    # canvas background
    s.append(rect(0, 0, 1460, 1090, fill=C["bg"], line=None, lw=0, name="canvasBg"))
    # title block
    s.append(text(OX, 30, "Kanjurmarg Station — Foot Overbridge Utilization", 22, "ink", True, name="titleText"))
    s.append(text(OX, 60, "Stochastic pedestrian-flow model · IE 301 Operational Analysis of Multimodal Interchange Hubs", 13, "muted"))
    s.append(text(OX, 82, "Simplified conceptual layout — not to scale", 12, "red", True, name="notToScale"))
    # layout card
    s.append(card(OX - 25, OY - 45, 80 * PX_PER_M + 50, 92 * PX_PER_M + 75))
    s.append(text(OX - 8, OY - 25, "STATION LAYOUT", 11, "muted", True))
    # north arrow
    nx, ny = X(76), OY - 30
    s.append(poly([(nx, ny + 18), (nx, ny - 6)], C["ink"], 2))
    s.append(poly([(nx - 5, ny + 2), (nx, ny - 8), (nx + 5, ny + 2)], C["ink"], 2, closed=True, fill=C["ink"]))
    s.append(text(nx + 9, ny - 2, "N", 12, "ink", True))

    top, bot = 2, 88
    # west street strip & concourse
    s.append(rect(X(0), Y(top), 8 * PX_PER_M, (bot - top) * PX_PER_M, fill=C["street"], name="westStreet"))
    s.append(rect(X(8), Y(top), 8 * PX_PER_M, (bot - top) * PX_PER_M, fill=C["concourse"], line=C["platform_edge"]))
    s.append(text(X(12), Y(bot) + 18, "West footpath", 10, "muted", align="CENTER"))
    # PF1 / 1A
    s.append(rect(X(18), Y(top), 12 * PX_PER_M, (bot - top) * PX_PER_M, fill=C["platform"], line=C["platform_edge"], name="pf1"))
    s.append(text(X(24), Y(71), "PF 1 / 1A", 13, "ink", True, "CENTER"))
    # tracks between PF1 and PF2
    for x0 in (30, 54):
        s.append(rect(X(x0), Y(top), 12 * PX_PER_M, (bot - top) * PX_PER_M, fill="#E3E6EA", line=None, lw=0))
        for rx in (x0 + 2.2, x0 + 3.8, x0 + 8.2, x0 + 9.8):
            s.append(poly([(X(rx), Y(top)), (X(rx), Y(bot))], C["rail"], 1.2))
    s.append(text(X(36), Y(bot) + 18, "Tracks", 10, "muted", align="CENTER"))
    s.append(text(X(60), Y(bot) + 18, "Tracks", 10, "muted", align="CENTER"))
    # PF2
    s.append(rect(X(42), Y(top), 12 * PX_PER_M, (bot - top) * PX_PER_M, fill=C["platform"], line=C["platform_edge"], name="pf2"))
    s.append(text(X(48), Y(71), "PF 2", 13, "ink", True, "CENTER"))
    # east side (context only)
    s.append(rect(X(66), Y(top), 12 * PX_PER_M, (bot - top) * PX_PER_M, fill=C["east"], line=C["cardline"], style="DASHED"))
    s.append(text(X(72), Y(40), "East side", 11, "faint", True, "CENTER"))
    s.append(text(X(72), Y(40) + 15, "(skywalk, NE/SE", 10, "faint", align="CENTER"))
    s.append(text(X(72), Y(40) + 28, "entrances —", 10, "faint", align="CENTER"))
    s.append(text(X(72), Y(40) + 41, "not modelled)", 10, "faint", align="CENTER"))

    # FOBs (deck drawn at its width in metres)
    def fob(yc, width_m, col, soft, label, closed=False, name=None):
        out = [rect(X(12), Y(yc - width_m / 2), 56 * PX_PER_M, width_m * PX_PER_M, fill=soft, line=col, lw=2,
                    name=name, style="DASHED" if closed else "SOLID")]
        out.append(text(X(64) - 4, Y(yc) - 6, label, 12, col, True, "RIGHT"))
        return out

    s += fob(10, 4.0, C["red"], C["red_soft"], "FOB 1 — CLOSED", closed=True, name="fob1Deck")
    for xx in (16, 24, 32, 40):
        s.append(poly([(X(xx), Y(8.6)), (X(xx + 3), Y(11.4))], C["red"], 2))
        s.append(poly([(X(xx), Y(11.4)), (X(xx + 3), Y(8.6))], C["red"], 2))
    s += fob(32, 5.36, C["teal"], C["teal_soft"], "FOB 2  (5.36 m)", name="fob2Deck")
    s += fob(62, 6.0, C["blue"], C["blue_soft"], "FOB 3  (6.0 m, assumed)", name="fob3Deck")
    # crossing-count lines at deck mid-points
    for yc, w, col in ((32, 5.36, C["teal"]), (62, 6.0, C["blue"])):
        s.append(poly([(X(36), Y(yc - w / 2)), (X(36), Y(yc + w / 2))], col, 2, style="DOTTED"))
    s.append(text(X(36) + 4, Y(32 + 2.68) + 12, "count line", 9, "teal"))
    s.append(text(X(36) + 4, Y(62 + 3.0) + 12, "count line", 9, "blue"))

    # entrances
    for name_, ym in (("Naval Colony", 16), ("Huma", 46), ("Gandhi Nagar", 78)):
        s.append(rect(X(0.5), Y(ym - 3), 7 * PX_PER_M, 6 * PX_PER_M, fill="#FFFFFF", line=C["ink"], lw=1.5))
        s.append(text(X(4), Y(ym) + 4, name_[0], 13, "ink", True, "CENTER"))
        s.append(text(X(4), Y(ym - 3) - 6, name_, 11, "ink", True, "CENTER"))

    # legend
    ly = Y(bot) + 42
    for i, (lab, col) in enumerate((("Direct to PF1", C["amber"]), ("Via FOB 2", C["teal"]), ("Via FOB 3", C["blue"]))):
        lx = X(2) + i * 150
        s.append(oval(lx, ly, 5, col, line="#FFFFFF"))
        s.append(text(lx + 12, ly + 4, lab, 12, "ink"))
    s.append(text(X(2) + 450, ly + 4, "1 dot = 1 passenger", 11, "muted"))
    return s


# ------------------------------------------------------------------ dashboard (right side)
DX = 730


def dashboard_shapes():
    s = []
    # --- header / scenario card
    y = OY - 45
    s.append(card(DX, y, 700, 72, accent=C["teal"]))
    s.append(text(DX + 18, y + 24, "Scenario", 11, "muted", True))
    s.append(text(DX + 18, y + 50, "", 18, "ink", True,
                  code='scenarioName + "   ·   demand × " + String.format("%.2f", demandMultiplier)', name="txtScenario"))
    s.append(text(DX + 420, y + 24, "Model clock (peak hour)", 11, "muted", True))
    s.append(text(DX + 420, y + 50, "", 18, "ink", True, font="Monospaced",
                  code='String.format("%02d:%02d / %d:00 min", (int)(time() / 60), (int)(time() % 60), durationMin) + (runFinished ? "  (done)" : "")',
                  name="txtClock"))

    # --- KPI row
    y = OY + 40
    kpis = [("Passengers generated", "String.format(\"%,d\", generated)"),
            ("Completed (left model)", "String.format(\"%,d\", completed)"),
            ("Walking now", "String.format(\"%,d\", passengers.size())"),
            ("Direct PF1 users", "String.format(\"%,d\", routeCount[0])")]
    for i, (lab, code) in enumerate(kpis):
        x = DX + i * 177
        s.append(card(x, y, 168, 62))
        s.append(text(x + 12, y + 20, lab, 10, "muted", True))
        s.append(text(x + 12, y + 47, "", 20, "ink", True, code=code, name=f"kpi{i}"))

    # --- FOB cards
    y = OY + 115
    for i, (fob, col, soft, idx) in enumerate((("FOB 2", C["teal"], C["teal_soft"], 2), ("FOB 3", C["blue"], C["blue_soft"], 3))):
        x = DX + i * 354
        s.append(card(x, y, 346, 170, accent=col))
        s.append(text(x + 18, y + 24, fob + ("  ·  W = 5.36 m" if idx == 2 else "  ·  W = 6.0 m (assumed)"), 14, col, True))
        s.append(text(x + 18, y + 44, "", 11, "muted",
                      code=f'String.format("Capacity C = W × 60 = %.1f pax/min", capacity{idx}())', name=f"txtCap{idx}"))
        s.append(text(x + 18, y + 72, "Crossings so far", 10, "muted", True))
        s.append(text(x + 18, y + 96, "", 20, "ink", True, code=f'String.format("%,d", fob{idx}Total)', name=f"txtTot{idx}"))
        s.append(text(x + 180, y + 72, "Last 1-min flow", 10, "muted", True))
        s.append(text(x + 180, y + 96, "", 20, "ink", True,
                      code=f'minutesDone == 0 ? "–" : String.format("%d pax", (int) lastFlow{idx})', name=f"txtLast{idx}"))
        s.append(text(x + 18, y + 116, "1-min utilization   now  ·  mean  ·  peak", 10, "muted", True))
        s.append(text(x + 18, y + 132, "", 13, "ink", True,
                      code=f'minutesDone == 0 ? "waiting for first full minute" : String.format("%.1f%%  ·  %.1f%%  ·  %.1f%%", lastU{idx}, sumU{idx} / minutesDone, peakU{idx})',
                      name=f"txtU{idx}"))
        s.append(rect(x + 18, y + 142, 250, 14, fill="#EEF1F4", line=None, lw=0))
        s.append(rect(x + 18, y + 142, 1, 14, fill=col, line=None, lw=0, name=f"barU{idx}"))
        s.append(text(x + 274, y + 154, "50%", 10, "muted"))
        s.append(poly([(x + 18 + 125, y + 140), (x + 18 + 125, y + 158)], C["faint"], 1, style="DOTTED"))
    # FOB 1 strip
    y = OY + 292
    s.append(card(DX, y, 700, 36, accent=C["red"]))
    s.append(text(DX + 18, y + 23, "FOB 1 — CLOSED · never offered as a route", 12, "red", True))
    s.append(text(DX + 682, y + 23, "", 12, "red", True, align="RIGHT",
                  code='String.format("crossings: %d", fob1Total)', name="txtFob1"))

    # --- route split card
    y = OY + 336
    s.append(card(DX, y, 700, 112))
    s.append(text(DX + 18, y + 22, "ROUTE SPLIT  —  aggregate-calibrated assumption (same at every entrance)", 11, "muted", True))
    rows = (("Direct PF1", "barRoutePF1", C["amber"], 0, "pDirectPF1"),
            ("Via FOB 2", "barRouteFOB2", C["teal"], 1, "pFOB2"),
            ("Via FOB 3", "barRouteFOB3", C["blue"], 2, "pFOB3"))
    for j, (lab, nm, col, r, par) in enumerate(rows):
        yy = y + 40 + j * 24
        s.append(text(DX + 18, yy + 11, lab, 12, "ink", True))
        s.append(rect(DX + 110, yy, 250, 14, fill="#EEF1F4", line=None, lw=0))
        s.append(rect(DX + 110, yy, 100, 14, fill=col, line=None, lw=0, name=nm))
        s.append(text(DX + 372, yy + 11, "", 12, "ink", True,
                      code=f'String.format("%.3f%% configured", routeProbs()[{r}] * 100)', name=f"txtP{r}"))
        s.append(text(DX + 540, yy + 11, "", 12, "muted",
                      code=f'generated == 0 ? "" : String.format("%.2f%% realised", 100.0 * routeCount[{r}] / generated)',
                      name=f"txtR{r}"))

    # --- charts
    y = OY + 456
    s.append(card(DX, y, 346, 220))
    s.append(text(DX + 14, y + 20, "One-minute utilization over time (%)", 12, "ink", True))
    s.append(card(DX + 354, y, 346, 220))
    s.append(text(DX + 368, y + 20, "Variability: distribution of 1-min utilization (%)", 12, "ink", True))

    # --- batch card
    y = OY + 684
    s.append(card(DX, y, 700, 236, accent=C["ink"]))
    s.append(text(DX + 18, y + 22, "REPLICATED EXPERIMENT  —  all three demand scenarios", 11, "muted", True))
    s.append(text(DX + 18, y + 42, "", 11, "muted",
                  code='String.format("%d replications × 3 scenarios, seeds %d–%d, %d min each. Results → anylogic_batch_results.csv", replications, randomSeed, randomSeed + replications - 1, durationMin)',
                  name="txtBatchInfo"))
    s.append(text(DX + 18, y + 66, "", 11, "ink", font="Monospaced",
                  code='batchDone ? batchSummary : "Press  Run replications  to run the batch (takes about a second)."',
                  name="txtBatch"))
    # comparison bars
    base = y + 214
    s.append(text(DX + 548, y + 22, "Mean utilization (%)", 11, "muted", True))
    s.append(poly([(DX + 520, base), (DX + 690, base)], C["faint"], 1))
    labels = ("Base", "+10%", "+20%")
    names = (("cmpBar_b2", "cmpBar_b3"), ("cmpBar_p2", "cmpBar_p3"), ("cmpBar_q2", "cmpBar_q3"))
    for k in range(3):
        bx = DX + 528 + k * 56
        s.append(rect(bx, base - 1, 20, 1, fill=C["teal"], line=None, lw=0, name=names[k][0]))
        s.append(rect(bx + 22, base - 1, 20, 1, fill=C["blue"], line=None, lw=0, name=names[k][1]))
        s.append(text(bx + 21, base + 13, labels[k], 10, "muted", align="CENTER"))
    return s


def controls():
    y = OY + 684
    return [
        button(DX + 18, y + 192, 170, 32, "Run replications", "runBatch();", "btnBatch"),
        button(DX + 198, y + 192, 150, 32, "Pause / Resume",
               "if (getEngine().getState() == Engine.State.RUNNING) getEngine().pause(); else getEngine().run();",
               "btnPause"),
    ]


def main_class():
    lvl = nid()
    pop_pres_id = nid()
    params = (
        parameter("scenarioName", "String", '"Baseline"', -350, 40, "Scenario name") +
        parameter("demandMultiplier", "double", "1.0", -350, 70, "Demand multiplier") +
        parameter("pDirectPF1", "double", "65.89 / 169.19", -350, 110, "P(direct PF1)") +
        parameter("pFOB2", "double", "70.00 / 169.19", -350, 140, "P(FOB 2)") +
        parameter("pFOB3", "double", "33.30 / 169.19", -350, 170, "P(FOB 3)") +
        parameter("randomSeed", "long", "1001", -350, 210, "Random seed") +
        parameter("durationMin", "int", "60", -350, 240, "Run duration (min)") +
        parameter("replications", "int", "30", -350, 270, "Replications (batch)") +
        parameter("fob2Width", "double", "5.36", -350, 310, "FOB 2 width (m)") +
        parameter("fob3Width", "double", "6.0", -350, 340, "FOB 3 width (m) - assumed") +
        parameter("flowIntensity", "double", "60", -350, 370, "Flow intensity I (pax/m/min)") +
        parameter("walkSpeed", "double", "1.30", -350, 400, "Walking speed (m/s)")
    )
    var_specs = [
        ("streamRng", "java.util.Random[]", None), ("generated", "int", "0"), ("completed", "int", "0"),
        ("routeCount", "int[]", "new int[3]"), ("fob1Total", "int", "0"), ("fob2Total", "int", "0"),
        ("fob3Total", "int", "0"), ("fob2PerMin", "int[]", None), ("fob3PerMin", "int[]", None),
        ("lastFlow2", "double", "0"), ("lastFlow3", "double", "0"), ("lastU2", "double", "0"),
        ("lastU3", "double", "0"), ("peakU2", "double", "0"), ("peakU3", "double", "0"),
        ("sumU2", "double", "0"), ("sumU3", "double", "0"), ("minutesDone", "int", "0"),
        ("runFinished", "boolean", "false"), ("batchDone", "boolean", "false"),
        ("batchSummary", "String", '""'), ("batchMeanU", "double[][]", "new double[3][2]"),
        ("batchP95U", "double[][]", "new double[3][2]"), ("cmpBaseY", "double", str(OY + 684 + 214)),
    ]
    variables = "".join(plain_var(n, t, i, -200, 40 + 26 * k) for k, (n, t, i) in enumerate(var_specs))
    events = cyclic_event("minuteTick", "60", "60", EV_MINUTE, -500, 40)
    dyn = (dynamic_event("Arrival", [("stream", "int")], EV_ARRIVAL, -500, 90) +
           dynamic_event("Waypoint", [("p", "Passenger")], EV_WAYPOINT, -500, 120) +
           dynamic_event("Crossing", [("route", "int")], EV_CROSSING, -500, 150))
    funcs = (
        function("routeProbs", "double[]", FN_ROUTE_PROBS, -500, 200, returns=True) +
        function("spawnPassenger", "double", FN_SPAWN, -500, 230, params=[("stream", "int"), ("route", "int")]) +
        function("advance", "double", FN_ADVANCE, -500, 260, params=[("p", "Passenger")]) +
        function("toPxX", "double", FN_TOPX, -500, 290, params=[("xMetres", "double")], returns=True) +
        function("toPxY", "double", FN_TOPY, -500, 320, params=[("yMetres", "double")], returns=True) +
        function("capacity2", "double", FN_CAP2, -500, 350, returns=True) +
        function("capacity3", "double", FN_CAP3, -500, 380, returns=True) +
        function("utilColor", "Color", FN_UTILCOLOR, -500, 410, params=[("u", "double")], returns=True) +
        function("updateRouteSplitBars", "double", FN_ROUTEBARS, -500, 440) +
        function("runBatch", "double", FN_BATCH, -500, 470)
    )
    analysis = histogram_data("utilHist2", -650, 40) + histogram_data("utilHist3", -650, 70)
    population = f"""
				<EmbeddedObject>
					<Id>{nid()}</Id>
					<Name>{cdata('passengers')}</Name>
					<X>-650</X><Y>120</Y>
					<Label><X>-30</X><Y>-30</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<PresentationId>{pop_pres_id}</PresentationId>
					<ActiveObjectClass>
						<PackageName>{cdata(PKG)}</PackageName>
						<ClassName>{cdata('Passenger')}</ClassName>
					</ActiveObjectClass>
					<GenericParameterSubstitute>
						<GenericParameterSubstituteReference>
							<PackageName>{cdata(PKG)}</PackageName>
							<ClassName>{cdata('Passenger')}</ClassName>
							<ItemName>{cdata(str(PASSENGER_GEN_ID))}</ItemName>
						</GenericParameterSubstituteReference>
					</GenericParameterSubstitute>
					<Parameters>
					</Parameters>
					<ReplicationFlag>true</ReplicationFlag>
					<Replication Class="CodeValue">
						<Code>{cdata('0')}</Code>
					</Replication>
					<CollectionType>ARRAY_LIST_BASED</CollectionType>
					<InEnvironment>true</InEnvironment>
					<InitialLocationType>AT_ANIMATION_POSITION</InitialLocationType>
					<XCode Class="CodeValue"><Code>{cdata('0')}</Code></XCode>
					<YCode Class="CodeValue"><Code>{cdata('0')}</Code></YCode>
					<ZCode Class="CodeValue"><Code>{cdata('0')}</Code></ZCode>
					<ColumnCode Class="CodeValue"><Code>{cdata('0')}</Code></ColumnCode>
					<RowCode Class="CodeValue"><Code>{cdata('0')}</Code></RowCode>
					<LatitudeCode Class="CodeValue"><Code>{cdata('0')}</Code></LatitudeCode>
					<LongitudeCode Class="CodeValue"><Code>{cdata('0')}</Code></LongitudeCode>
					<LocationNameCode Class="CodeValue"><Code>{cdata('""')}</Code></LocationNameCode>
					<InitializationType>SPECIFIED_NUMBER</InitializationType>
					<InitializationDatabaseTableQuery>
						<TableReference>
						</TableReference>
					</InitializationDatabaseTableQuery>
					<InitializationDatabaseType>ONE_AGENT_PER_DATABASE_RECORD</InitializationDatabaseType>
					<QuantityColumn>
					</QuantityColumn>
				</EmbeddedObject>"""
    pop_pres = f"""
				<EmbeddedObjectPresentation>
					<Id>{pop_pres_id}</Id>
					<Name>{cdata('passengers_presentation')}</Name>
					<X>0</X><Y>0</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>true</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>false</ShowLabel>
					<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
					<EmbeddedIcon>false</EmbeddedIcon>
					<Z>0</Z>
					<Rotation>0.0</Rotation>
					<DrawingMode>POSITION_WITH_OFFSET</DrawingMode>
					<ScaleType>AUTOMATICALLY_CALCULATED</ScaleType>
					<GISScaleForRealEmbeddedObjectPresentationSize>1000</GISScaleForRealEmbeddedObjectPresentationSize>
					<GISScaleForFixedEmbeddedObjectPresentationSize>1000000000</GISScaleForFixedEmbeddedObjectPresentationSize>
					<Latitude>0.0</Latitude>
					<Longitude>0.0</Longitude>
				</EmbeddedObjectPresentation>"""
    yc = OY + 456
    charts = (time_plot("utilPlot", DX + 6, yc + 30, 334, 186,
                        [("FOB 2", "lastU2", C["teal"]), ("FOB 3", "lastU3", C["blue"])], 40) +
              histogram_chart("utilHistogram", DX + 360, yc + 30, 334, 186,
                              [("FOB 2", "utilHist2", C["teal"]), ("FOB 3", "utilHist3", C["blue"])]))
    shapes = "\n".join(layout_shapes()) + "\n" + "\n".join(dashboard_shapes())
    # shapes first (background), then agents, then charts/controls on top
    presentation = shapes + pop_pres + charts + "\n".join(controls())

    import_code = "import java.awt.Color;"
    extra = (f"<AdditionalClassCode>{cdata(MAIN_ADDITIONAL)}</AdditionalClassCode>"
             f"<Import>{cdata(import_code)}</Import><StartupCode>{cdata(STARTUP)}</StartupCode>")
    return agent_header(MAIN_CLASS_ID, "Main", MAIN_GEN_ID, extra) + agent_props() + env_props(1460, 1090) + \
        scale_ruler(False) + f"""
			<CurrentLevel>{lvl}</CurrentLevel>
			<ConnectionsId>{nid()}</ConnectionsId>
			<Variables>{params}{variables}
			</Variables>
			<Events>{events}
			</Events>
			<DynamicEvents>{dyn}
			</DynamicEvents>
			<Functions>{funcs}
			</Functions>
			<AnalysisData>{analysis}
			</AnalysisData>
			<EmbeddedObjects>{population}
			</EmbeddedObjects>
			<Presentation>
				<Level>
					<Id>{lvl}</Id>
					<Name>{cdata('level')}</Name>
					<X>0</X><Y>0</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>true</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>false</ShowLabel>
					<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
					<Z>0</Z>
					<LevelVisibility>DIM_NON_CURRENT</LevelVisibility>
			<Presentation>
{presentation}
			</Presentation>
				</Level>
			</Presentation>
		</ActiveObjectClass>"""


def experiment():
    ex_vars = (plain_var("scenarioIdx", "int", "0", -100, 40) + plain_var("seedVal", "int", "1001", -100, 70) +
               plain_var("repsVal", "int", "30", -100, 100) + plain_var("durVal", "int", "60", -100, 130) +
               plain_var("w3Val", "double", "6.0", -100, 160))
    pres = [
        rect(0, 0, 900, 600, fill=C["bg"], line=None, lw=0),
        card(40, 30, 820, 110, accent=C["teal"]),
        text(62, 70, "Kanjurmarg FOB Utilization — Stochastic Simulation", 22, "ink", True),
        text(62, 98, "IE 301 · Poisson arrivals at Naval Colony, Huma and Gandhi Nagar · aggregate-calibrated route split", 13, "muted"),
        text(62, 122, "Simplified conceptual layout — not to scale · FOB 1 closed", 12, "red", True),
        card(40, 160, 400, 230),
        text(60, 188, "DEMAND SCENARIO", 11, "muted", True),
        radio(60, 205, 360, 100, ["Baseline (×1.00)", "Increased demand (×1.10)", "High increased demand (×1.20)"],
              "scenarioIdx", "rbScenario"),
        text(60, 330, "Demand increases are hypothetical (possible metro", 11, "muted"),
        text(60, 346, "integration), not ridership forecasts.", 11, "muted"),
        card(460, 160, 400, 230),
        text(480, 188, "RUN SETTINGS", 11, "muted", True),
    ]
    rows = [("Random seed", "seedVal", 0, None), ("Replications (batch)", "repsVal", 2, 500),
            ("Run duration (min)", "durVal", 1, 600), ("FOB 3 width (m, assumed)", "w3Val", 1, 20)]
    for i, (lab, link, mn, mx) in enumerate(rows):
        yy = 210 + i * 42
        pres.append(text(480, yy + 19, lab, 13, "ink"))
        pres.append(edit_box(700, yy, 140, link, f"eb_{link}", mn, mx))
    pres += [
        card(40, 410, 820, 120),
        text(60, 438, "HOW TO USE", 11, "muted", True),
        text(60, 462, "1. Choose a scenario and settings, then press Run.  2. Watch passengers walk (amber = direct PF1, teal = FOB 2, blue = FOB 3).", 12, "ink"),
        text(60, 482, "3. The live dashboard shows 1-minute FOB utilization U = Q / (W × 60) × 100%.  The run pauses at the end of the horizon.", 12, "ink"),
        text(60, 502, "4. Press 'Run replications' in the model to run all three scenarios with the chosen number of seeds (95% CIs).", 12, "ink"),
    ]
    params_xml = ""
    pmap = {
        "scenarioName": 'scenarioIdx == 0 ? "Baseline" : (scenarioIdx == 1 ? "+10% demand" : "+20% demand")',
        "demandMultiplier": "scenarioIdx == 0 ? 1.00 : (scenarioIdx == 1 ? 1.10 : 1.20)",
        "pDirectPF1": None, "pFOB2": None, "pFOB3": None,
        "randomSeed": "seedVal", "durationMin": "durVal", "replications": "repsVal",
        "fob2Width": None, "fob3Width": "w3Val", "flowIntensity": None, "walkSpeed": None,
    }
    for k, v in pmap.items():
        val = "" if v is None else f"<ParameterValue Class=\"CodeValue\"><Code>{cdata(v)}</Code></ParameterValue>"
        params_xml += f"<Parameter><ParameterName>{cdata(k)}</ParameterName>{val}</Parameter>\n"
    return f"""
		<SimulationExperiment ActiveObjectClassId="{MAIN_CLASS_ID}">
			<Id>{nid()}</Id>
			<Name>{cdata('Simulation')}</Name>
			<CommandLineArguments>{cdata('')}</CommandLineArguments>
			<MaximumMemory>1024</MaximumMemory>
			<RandomNumberGenerationType>fixedSeed</RandomNumberGenerationType>
			<CustomGeneratorCode>new Random()</CustomGeneratorCode>
			<SeedValue>1001</SeedValue>
			<SelectionModeForSimultaneousEvents>LIFO</SelectionModeForSimultaneousEvents>
			<VmArgs>{cdata('')}</VmArgs>
			<LoadRootFromSnapshot>false</LoadRootFromSnapshot>
			<Variables>{ex_vars}
			</Variables>
			<Presentation>
{chr(10).join(pres)}
			</Presentation>
			<Parameters>
{params_xml}
			</Parameters>
			<PresentationProperties>
				<EnableZoomAndPanning>true</EnableZoomAndPanning>
				<ExecutionMode>{cdata('realTimeScaled')}</ExecutionMode>
				<Title>{cdata('Kanjurmarg FOB Utilization : Simulation')}</Title>
				<EnableDeveloperPanel>true</EnableDeveloperPanel>
				<ShowDeveloperPanelOnStart>false</ShowDeveloperPanelOnStart>
				<RealTimeScale>10.0</RealTimeScale>
			</PresentationProperties>
			<ModelTimeProperties>
				<StopOption>{cdata('Never')}</StopOption>
				<InitialDate>{cdata('1761535800000')}</InitialDate>
				<InitialTime>{cdata('0.0')}</InitialTime>
				<FinalDate>{cdata('1761539400000')}</FinalDate>
				<FinalTime>{cdata('3600.0')}</FinalTime>
			</ModelTimeProperties>
			<BypassInitialScreen>false</BypassInitialScreen>
		</SimulationExperiment>"""


def build():
    model_id = nid()
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
*************************************************
	         AnyLogic Project File
*************************************************
-->
<AnyLogicWorkspace WorkspaceVersion="1.9" AnyLogicVersion="8.8.6.202312140435" AlpVersion="8.8.3">
<Model>
	<Id>{model_id}</Id>
	<Name>{cdata(MODEL_NAME)}</Name>
	<Description>{cdata('Stochastic simulation of foot-overbridge (FOB) utilization at Kanjurmarg railway station under baseline, +10% and +20% hypothetical peak-hour demand. Poisson arrivals at Naval Colony, Huma and Gandhi Nagar; aggregate-calibrated route split between direct PF1 access, FOB 2 and FOB 3; FOB 1 closed. Simplified conceptual layout - not to scale. IE 301 project.')}</Description>
	<EngineVersion>6</EngineVersion>
	<JavaPackageName>{cdata(PKG)}</JavaPackageName>
	<ModelTimeUnit>{cdata('Second')}</ModelTimeUnit>
	<ActiveObjectClasses>
		<!--   =========   Active Object Class   ========  -->{main_class()}
		<!--   =========   Active Object Class   ========  -->{passenger_class()}
	</ActiveObjectClasses>
	<DifferentialEquationsMethod>EULER</DifferentialEquationsMethod>
	<MixedEquationsMethod>RK45_NEWTON</MixedEquationsMethod>
	<AlgebraicEquationsMethod>MODIFIED_NEWTON</AlgebraicEquationsMethod>
	<AbsoluteAccuracy>1.0E-5</AbsoluteAccuracy>
	<FixedTimeStep>0.001</FixedTimeStep>
	<RelativeAccuracy>1.0E-5</RelativeAccuracy>
	<TimeAccuracy>1.0E-5</TimeAccuracy>
	<Frame>
		<Width>1460</Width>
		<Height>1090</Height>
	</Frame>
	<Database>
		<Logging>false</Logging>
		<AutoExport>false</AutoExport>
		<ShutdownCompact>false</ShutdownCompact>
		<ImportSettings>
		</ImportSettings>
		<ExportSettings>
		</ExportSettings>
	</Database>

	<RunConfiguration ActiveObjectClassId="{MAIN_CLASS_ID}">
		<Id>{nid()}</Id>
		<Name>{cdata('RunConfiguration')}</Name>
		<MaximumMemory>1024</MaximumMemory>
		<ModelTimeProperties>
			<StopOption>{cdata('Never')}</StopOption>
			<InitialDate>{cdata('1761535800000')}</InitialDate>
			<InitialTime>{cdata('0.0')}</InitialTime>
			<FinalDate>{cdata('1761539400000')}</FinalDate>
			<FinalTime>{cdata('3600.0')}</FinalTime>
		</ModelTimeProperties>
		<AnimationProperties>
			<StopNever>true</StopNever>
			<ExecutionMode>realTimeScaled</ExecutionMode>
			<RealTimeScale>10.0</RealTimeScale>
			<EnableZoomAndPanning>true</EnableZoomAndPanning>
			<EnableDeveloperPanel>false</EnableDeveloperPanel>
			<ShowDeveloperPanelOnStart>false</ShowDeveloperPanelOnStart>
		</AnimationProperties>
		<Inputs>
		</Inputs>
		<Outputs>
		</Outputs>
	</RunConfiguration>
	<Experiments>
		<!--   =========   Simulation Experiment   ========  -->{experiment()}
	</Experiments>
    <RequiredLibraryReference>
		<LibraryName>{cdata('com.anylogic.libraries.modules.markup_descriptors')}</LibraryName>
		<VersionMajor>1</VersionMajor>
		<VersionMinor>0</VersionMinor>
		<VersionBuild>0</VersionBuild>
    </RequiredLibraryReference>
</Model>
</AnyLogicWorkspace>
"""
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, MODEL_NAME + ".alp")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(xml)
    print("wrote", path, len(xml), "bytes")
    return path


if __name__ == "__main__":
    build()
